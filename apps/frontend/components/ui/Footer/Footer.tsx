import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="lg:max-w-4xl px-6 mx-auto m-auto my-8 rounded-md">
      {/* Make list inline */}
      <ul className="flex justify-between flex-initial md:flex-1 ">
        <li className="py-3 md:py-0 md:pb-4">
          <Link
            href="/privacy-policy"
            className="dark:text-white text-zinc-800 transition duration-150 ease-in-out hover:text-zinc-200"
          >
            Privacy Policy
          </Link>
        </li>
        <li className="py-3 md:py-0 md:pb-4">
          <Link
            href="/terms-and-condition"
            className="dark:text-white text-zinc-800 transition duration-150 ease-in-out hover:text-zinc-200"
          >
            Terms of Use
          </Link>
        </li>
        <li className="py-3 md:py-0 md:pb-4">
          <Link
            href="/status"
            className="dark:text-white text-zinc-800 transition duration-150 ease-in-out hover:text-zinc-200"
          >
            Status
          </Link>
        </li>
      </ul>
   
    </footer>
  );
}
