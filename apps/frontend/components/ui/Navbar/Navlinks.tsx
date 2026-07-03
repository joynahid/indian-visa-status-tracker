'use client';

import Link from 'next/link';
import Logo from '@/components/icons/Logo';
import s from './Navbar.module.css';
import ThemeSwitch from '@/components/themeswitcher';

interface NavlinksProps {
  user?: any;
}

export default function Navlinks() {
  return (
    <div className="relative dark:text-zinc-200 text-zinc-900 flex flex-row justify-between p-4 align-center md:py-6">
      <div className="w-full flex items-center justify-between">
        <nav className="space-x-2 lg:block">
          <Link href="/" className="text-zinc-900 dark:text-zinc-200 font-medium">
            Indian Visa Status
          </Link>
        </nav>

        <ThemeSwitch />
      </div>
    </div>
  );
}
