import Navlinks from './Navlinks';

export default async function Navbar() {

  return (
    <nav>
      <div className="lg:max-w-4xl dark:bg-zinc-900 lg:rounded-md lg:my-4 mx-auto">
        <Navlinks />
      </div>
    </nav>
  );
}
