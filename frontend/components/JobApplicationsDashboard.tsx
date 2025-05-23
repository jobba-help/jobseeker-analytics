"use client";

import React, { useState, useEffect } from "react";
import { Table, TableHeader, TableBody, TableColumn, TableRow, TableCell } from "@heroui/table";
import { DatePicker } from "@heroui/react";
import { CalendarDate } from "@internationalized/date";
import { useRouter } from "next/navigation";
import {
	Button,
	Dropdown,
	DropdownItem,
	DropdownMenu,
	DropdownSection,
	DropdownTrigger,
	Modal,
	ModalBody,
	ModalContent,
	ModalFooter,
	ModalHeader,
	Tooltip
} from "@heroui/react";

import { DownloadIcon, SortIcon, TrashIcon } from "@/components/icons";

export interface Application {
	id?: string;
	company_name: string;
	application_status: string;
	received_at: string;
	job_title: string;
	subject: string;
	email_from: string;
	job_summary: string;
}

interface JobApplicationsDashboardProps {
	title?: string;
	data: Application[];
	loading: boolean;
	downloading: boolean;
	onDownloadCsv: () => void;
	onDownloadSankey: () => void;
	onRemoveItem: (id: string) => void;
	initialSortKey?: string;
	responseRate?: React.ReactNode;
	onNextPage: () => void;
	onPrevPage: () => void;
	currentPage: number;
	totalPages: number;
}

// Load sort key from localStorage or use default
const getInitialSortKey = (key: string) => {
	return typeof window !== "undefined" ? localStorage.getItem("sortKey") || key : key;
};

export default function JobApplicationsDashboard({
	title = "Job Applications Dashboard",
	data,
	loading,
	downloading,
	onDownloadCsv,
	onDownloadSankey,
	onRemoveItem, // Accept the callback
	initialSortKey = "Date (Newest)",
	responseRate
}: JobApplicationsDashboardProps) {
	const [sortedData, setSortedData] = useState<Application[]>([]);
	const [selectedKeys, setSelectedKeys] = useState(new Set([getInitialSortKey(initialSortKey)]));
	const [showModal, setShowModal] = useState(false);
	const [selectedDate, setSelectedDate] = useState<CalendarDate | null>(null);
	const [isSaving, setIsSaving] = useState(false);
	const [isNewUser, setIsNewUser] = useState(false);
	const [showSummaryModal, setShowSummaryModal] = useState(false);
	const [selectedSummary, setSelectedSummary] = useState<string>("");
	const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
	const router = useRouter();
	const [showDelete, setShowDelete] = useState(false);
	const [itemToRemove, setItemToRemove] = useState<string | null>(null);

	const [currentPage, setCurrentPage] = useState(1);
	const pageSize = 10;

	const selectedValue = React.useMemo(() => Array.from(selectedKeys).join(", ").replace(/_/g, ""), [selectedKeys]);

	const handleSave = async () => {
		if (!selectedDate) return alert("Please select a start date");

		setIsSaving(true);
		const formattedDate = `${selectedDate.year}-${String(selectedDate.month).padStart(2, "0")}-${String(selectedDate.day).padStart(2, "0")}`;
		// Step 1: Save the start date
		const response = await fetch(`${apiUrl}/set-start-date`, {
			method: "POST",
			headers: { "Content-Type": "application/x-www-form-urlencoded" },
			body: new URLSearchParams({ start_date: formattedDate.toString() }),
			credentials: "include"
		});

		if (!response.ok) throw new Error("Failed to save start date");

		// Step 2: Start background task (fetch emails)
		startFetchEmailsBackgroundTask();

		// Step 3: Navigate to processing page
		setIsNewUser(false); // Hide the modal after saving
		setShowModal(false);
		router.push("/processing"); // Navigate to the processing page
	};

	const startFetchEmailsBackgroundTask = async () => {
		// Example background task: Start fetching emails
		const response = await fetch(`${apiUrl}/fetch-emails`, {
			method: "POST", // or GET, depending on your API
			credentials: "include"
		});

		if (!response.ok) {
			return;
		}
	};

	useEffect(() => {
		setShowModal(isNewUser);
	}, [isNewUser]);

	useEffect(() => {
		async function fetchSessionData() {
			const response = await fetch(`${apiUrl}/api/session-data`, {
				method: "GET",
				credentials: "include"
			});
			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}
			const data = await response.json();
			setIsNewUser(!!data.is_new_user); // Set the new user flag
			setShowModal(!!data.is_new_user); // Show modal if new user
		}
		fetchSessionData();
	}, []);

	// Sort data based on selected key
	useEffect(() => {
		const sortData = () => {
			const sorted = [...data];
			const sortKey = Array.from(selectedKeys)[0];

			switch (sortKey) {
				case "Date (Newest)":
					sorted.sort((a, b) => new Date(b.received_at).getTime() - new Date(a.received_at).getTime());
					break;
				case "Date (Oldest)":
					sorted.sort((a, b) => new Date(a.received_at).getTime() - new Date(b.received_at).getTime());
					break;
				case "Company":
					sorted.sort((a, b) => a.company_name.localeCompare(b.company_name));
					break;
				case "Job Title":
					sorted.sort((a, b) => a.job_title.localeCompare(b.job_title));
					break;
				case "Status":
					sorted.sort((a, b) => a.application_status.localeCompare(b.application_status));
					break;
				default:
					break;
			}
			setSortedData(sorted);
		};

		if (data.length > 0) {
			sortData();
		} else {
			setSortedData([]);
		}
	}, [selectedKeys, data]);

	const paginatedData = sortedData.slice((currentPage - 1) * pageSize, currentPage * pageSize);

	// Handle sorting selection change and store it in localStorage
	const handleSortChange = (keys: Set<string>) => {
		const sortKey = Array.from(keys)[0];
		localStorage.setItem("sortKey", sortKey);
		setSelectedKeys(new Set([sortKey]));
	};

	// Pagination controls
	const handleNextPage = () => {
		if (currentPage < Math.ceil(sortedData.length / pageSize)) {
			setCurrentPage(currentPage + 1);
		}
	};

	const handlePreviousPage = () => {
		if (currentPage > 1) {
			setCurrentPage(currentPage - 1);
		}
	};

	const handlePageChange = (page: number) => {
		setCurrentPage(page);
	};

	const totalPages = Math.ceil(sortedData.length / pageSize);

	return (
		<div className="p-6">
			{/* Modal for New User */}
			<Modal isOpen={showModal} onOpenChange={setShowModal}>
				<ModalContent>
					<ModalHeader>Select Your Job Search Start Date</ModalHeader>
					<ModalBody>
						<DatePicker value={selectedDate} onChange={setSelectedDate} />
					</ModalBody>
					<ModalFooter>
						<Button color="primary" isLoading={isSaving} onPress={handleSave}>
							Save and Continue
						</Button>
					</ModalFooter>
				</ModalContent>
			</Modal>
			<Modal isOpen={showDelete} onOpenChange={(isOpen) => setShowDelete(isOpen)}>
				<ModalContent>
					{(onClose) => (
						<>
							<ModalHeader className="flex flex-col gap-1">Confirm Removal</ModalHeader>
							<ModalBody>
								<p>
									Are you sure you want to remove this row? Every job application impacts your
									metrics, so it's important to keep all records unless we accidentally made a mistake
									and picked up a non-job-related record.
								</p>
							</ModalBody>
							<ModalFooter>
								<Button color="default" variant="ghost" onPress={onClose}>
									Cancel
								</Button>
								<Button
									color="danger"
									onPress={() => {
										if (itemToRemove) {
											onRemoveItem(itemToRemove); // Notify the parent to remove the item
											setItemToRemove(null); // Clear the selected item
											setShowDelete(false); // Close the modal
										}
									}}
								>
									Yes, remove it
								</Button>
							</ModalFooter>
						</>
					)}
				</ModalContent>
			</Modal>
			<h1 className="text-2xl font-bold mt-0">{title}</h1>
			{responseRate}
			<div className="flex flex-wrap items-center justify-end gap-4 mb-4">
				<Dropdown>
					<DropdownTrigger>
						<Button
							className="pl-3"
							color="primary"
							data-testid="Sort By"
							isDisabled={!data || data.length === 0}
							startContent={<SortIcon />}
							variant="bordered"
						>
							{selectedValue}
						</Button>
					</DropdownTrigger>
					<DropdownMenu
						disallowEmptySelection
						aria-label="Single selection example"
						selectedKeys={selectedKeys}
						selectionMode="single"
						variant="flat"
						onSelectionChange={(keys) => handleSortChange(keys as Set<string>)}
					>
						<DropdownSection title="Sort By">
							<DropdownItem key="Date (Newest)">Date Received (Newest First)</DropdownItem>
							<DropdownItem key="Date (Oldest)">Date Received (Oldest First)</DropdownItem>
							<DropdownItem key="Company">Company (A-Z)</DropdownItem>
							<DropdownItem key="Job Title">Job Title (A-Z)</DropdownItem>
							<DropdownItem key="Status">Application Status</DropdownItem>
						</DropdownSection>
					</DropdownMenu>
				</Dropdown>
				<Button
					className="w-full sm:w-auto text-white"
					color="primary"
					isDisabled={!data || data.length === 0}
					isLoading={downloading}
					startContent={<DownloadIcon />}
					onPress={onDownloadSankey}
				>
					Download Sankey Diagram
				</Button>
				<Button
					className="w-full sm:w-auto text-white"
					color="success"
					isDisabled={!data || data.length === 0}
					isLoading={downloading}
					startContent={<DownloadIcon />}
					onPress={onDownloadCsv}
				>
					Download CSV
				</Button>
			</div>

			{loading ? (
				<p>Loading applications...</p>
			) : (
				<div className="overflow-x-auto bg-white dark:bg-black shadow-md rounded-lg">
					<Table aria-label="Applications Table">
						<TableHeader>
							<TableColumn>Company</TableColumn>
							<TableColumn>Status</TableColumn>
							<TableColumn>Received</TableColumn>
							<TableColumn>Job Title</TableColumn>
							<TableColumn>Subject</TableColumn>
							<TableColumn>Sender</TableColumn>
							<TableColumn>Job Summary</TableColumn>
							<TableColumn>Actions</TableColumn>
						</TableHeader>
						<TableBody>
							{paginatedData.map((item) => (
								<TableRow
									key={item.id || item.received_at}
									className="hover:bg-default-100 transition-colors"
								>
									<TableCell>{item.company_name || "--"}</TableCell>
									<TableCell>
										<span
											className={`inline-flex items-center justify-center px-2 py-1 rounded ${
												item.application_status.toLowerCase() === "rejected"
													? "bg-red-100 text-red-800"
													: "bg-green-100 text-green-800"
											}`}
										>
											{item.application_status || "--"}
										</span>
									</TableCell>
									<TableCell>{new Date(item.received_at).toLocaleDateString() || "--"}</TableCell>
									<TableCell>{item.job_title || "--"}</TableCell>
									<TableCell className="max-w-[300px] truncate">{item.subject || "--"}</TableCell>
									<TableCell>{item.email_from || "--"}</TableCell>
									<TableCell>
										<Button
											size="sm"
											variant="light"
											onPress={() => {
												setSelectedSummary(item.job_summary || "No job summary available");
												setShowSummaryModal(true);
											}}
										>
											View Job Description
										</Button>
									</TableCell>
									<TableCell className="text-center">
										<Tooltip content="Remove">
											<Button
												isIconOnly
												size="sm"
												variant="light"
												onPress={() => {
													setItemToRemove(item.id || null);
													setShowDelete(true);
												}}
											>
												<TrashIcon className="text-gray-800 dark:text-gray-300" />
											</Button>
										</Tooltip>
									</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				</div>
			)}
			<div className="flex justify-between items-center mt-4">
				<Button disabled={currentPage === 1} onPress={handlePreviousPage}>
					Previous
				</Button>
				<span>{`${currentPage} of ${totalPages}`}</span>
				<Button disabled={currentPage === totalPages} onPress={handleNextPage}>
					Next
				</Button>
			</div>

			{/* Job Summary Modal */}
			<Modal isOpen={showSummaryModal} onOpenChange={setShowSummaryModal}>
				<ModalContent>
					<ModalHeader>Job Summary</ModalHeader>
					<ModalBody>
						<div className="whitespace-pre-wrap">{selectedSummary}</div>
					</ModalBody>
					<ModalFooter>
						<Button color="primary" onPress={() => setShowSummaryModal(false)}>
							Close
						</Button>
					</ModalFooter>
				</ModalContent>
			</Modal>
		</div>
	);
}
