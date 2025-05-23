"use client";

import {
	Navbar as HeroUINavbar,
	NavbarContent,
	NavbarMenuToggle,
	NavbarBrand,
	NavbarItem,
	NavbarMenu,
	NavbarMenuItem,
	Button,
	Link,
	Tooltip
} from "@heroui/react";
import { useRouter } from "next/navigation";
import { usePathname } from "next/navigation";
import NextLink from "next/link";

import { siteConfig } from "@/config/site";
import { ThemeSwitch } from "@/components/theme-switch";
import { GithubIcon, HeartFilledIcon, GoogleIcon, LogOutIcon, InfoIcon } from "@/components/icons";

export const Navbar = () => {
	const pathname = usePathname();
	const router = useRouter();

	const apiUrl = process.env.NEXT_PUBLIC_API_URL!;

	const handleGoogleLogin = () => {
		router.push(`${apiUrl}/login`);
	};

	const handleGoogleLogout = async () => {
		router.push(`${apiUrl}/logout`);
	};

	const loginTooltipContent = (
		<div className="px-1 py-2 max-w-xs">
			<div className="text-sm font-bold mb-1">Beta Users Only</div>
			<div className="text-xs">
				This login is only for existing beta users. If you're not a beta user yet, please join our waitlist
				below.
			</div>
		</div>
	);

	return (
		<HeroUINavbar
			isBordered
			className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
			maxWidth="xl"
		>
			<NavbarContent className="basis-1/5 sm:basis-full" justify="start">
				<NavbarBrand as="li" className="gap-3 max-w-fit">
					<NextLink className="flex justify-start items-center gap-1" href="/">
						<div className="flex items-center gap-2">
							<span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-indigo-600">
								jobba.help
							</span>
							<span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full">Beta</span>
						</div>
					</NextLink>
				</NavbarBrand>
			</NavbarContent>

			<NavbarContent className="hidden md:flex basis-1/5 sm:basis-full" justify="end">
				<NavbarItem className="flex gap-2">
					<Link isExternal aria-label="Github" href={siteConfig.links.github}>
						<GithubIcon className="text-default-500" />
					</Link>
					<ThemeSwitch />
				</NavbarItem>
				<NavbarItem>
					<Button
						isExternal
						as={Link}
						className="text-sm font-normal text-default-600 bg-default-100"
						data-testid="Sponsor"
						href={siteConfig.links.sponsor}
						startContent={<HeartFilledIcon className="text-danger" />}
						variant="flat"
					>
						Sponsor
					</Button>
				</NavbarItem>
				<NavbarItem>
					{pathname === "/" ? (
						<Tooltip
							closeDelay={0}
							color="foreground"
							content={loginTooltipContent}
							delay={200}
							placement="bottom"
						>
							<Button
								className="w-full text-sm font-normal text-default-600 bg-default-100"
								data-testid="GoogleLogin"
								endContent={<InfoIcon className="text-default-400" size={14} />}
								startContent={<GoogleIcon className="text-danger" />}
								variant="flat"
								onPress={handleGoogleLogin}
							>
								Login with Google
							</Button>
						</Tooltip>
					) : (
						<Button
							className="w-full text-sm font-normal text-default-600 bg-default-100"
							data-testid="GoogleLogout"
							startContent={<LogOutIcon />}
							variant="flat"
							onPress={handleGoogleLogout}
						>
							Logout
						</Button>
					)}
				</NavbarItem>
			</NavbarContent>

			{/* Smaller screens */}
			<NavbarContent className="md:hidden" justify="end">
				{pathname === "/" ? (
					<Tooltip
						closeDelay={0}
						color="foreground"
						content={loginTooltipContent}
						delay={200}
						placement="bottom"
					>
						<Button
							className="w-auto text-sm font-normal text-default-600 bg-default-100"
							data-testid="GoogleLoginSmallScreen"
							endContent={<InfoIcon className="text-default-400" size={14} />}
							startContent={<GoogleIcon className="text-danger" />}
							variant="flat"
							onPress={handleGoogleLogin}
						>
							Login
						</Button>
					</Tooltip>
				) : (
					<Button
						className="w-auto text-sm font-normal text-default-600 bg-default-100 px-7"
						data-testid="GoogleLogoutSmallScreen"
						startContent={<LogOutIcon />}
						variant="flat"
						onPress={handleGoogleLogout}
					>
						Logout
					</Button>
				)}
				<NavbarMenuToggle />
			</NavbarContent>

			<NavbarMenu className="flex flex-col items-center gap-3">
				<NavbarMenuItem>
					<Link
						isExternal
						aria-label="Github"
						className="w-auto flex items-center justify-center gap-2 text-sm font-medium text-default-600 hover:text-default-900 bg-default-100 px-4 py-2 rounded-md transition"
						href={siteConfig.links.github}
					>
						<GithubIcon className="w-5 h-5 text-default-500" />
						<span>View code</span>
					</Link>
				</NavbarMenuItem>

				<NavbarMenuItem>
					<ThemeSwitch className="w-auto flex items-center justify-center gap-2 text-sm font-medium text-default-600 hover:text-default-900 bg-default-100 px-4 py-2 rounded-md transition">
						<span>Change theme</span>
					</ThemeSwitch>
				</NavbarMenuItem>

				<NavbarMenuItem>
					<Button
						isExternal
						as={Link}
						className="w-auto text-sm font-medium text-default-600 bg-default-100 px-4 py-2 rounded-md transition"
						href={siteConfig.links.sponsor}
						startContent={<HeartFilledIcon className="text-danger" />}
						variant="flat"
					>
						Sponsor
					</Button>
				</NavbarMenuItem>
			</NavbarMenu>
		</HeroUINavbar>
	);
};
