'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="bg-blue-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="text-2xl font-bold">
            Brain
          </Link>

          <div className="hidden md:flex space-x-1">
            <NavLink href="/documents">Documents</NavLink>
            <NavLink href="/search">Search</NavLink>
            <NavLink href="/pending-review">Pending</NavLink>
            <NavLink href="/reports">Reports</NavLink>
          </div>

          <button
            className="md:hidden"
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {isOpen && (
          <div className="md:hidden pb-4 space-y-2">
            <MobileNavLink href="/documents">Documents</MobileNavLink>
            <MobileNavLink href="/search">Search</MobileNavLink>
            <MobileNavLink href="/pending-review">Pending</MobileNavLink>
            <MobileNavLink href="/reports">Reports</MobileNavLink>
          </div>
        )}
      </div>
    </nav>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-800 transition"
    >
      {children}
    </Link>
  );
}

function MobileNavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-800 transition"
    >
      {children}
    </Link>
  );
}
