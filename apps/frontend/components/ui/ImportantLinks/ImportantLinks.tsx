import { MessageSquare, UsersRound } from 'lucide-react';
import { ReactNode } from 'react';

interface RowProps {
  url: string;
  title: string;
  icon: ReactNode;
  bgClass?: string;
}

function Row({ url, title, icon, bgClass }: RowProps) {
  return (
    <div className={`lg:max-w-4xl mx-auto py-2 my-2 rounded-md dark:text-zinc-500 ${bgClass ?? ''}`}>
      <a
        className="flex items-center gap-2 text-sm px-6 dark:text-white text-slate-900"
        href={url}
        target="_blank"
        rel="noopener noreferrer"
      >
        {icon}
        {title}
      </a>
    </div>
  );
}

// Homepage that shows greetings and quick card links to navigate to other pages
export default function ImportantLinks() {
  return (
    <>
      <Row
        url="https://www.facebook.com/profile.php?id=61559092887780"
        bgClass="bg-blue-200 dark:bg-blue-900"
        title="Follow us on Facebook"
        icon={
          <svg
            xmlns="http://www.w3.org/2000/svg"
            x="0px"
            y="0px"
            width="20"
            height="20"
            viewBox="0 0 48 48"
            className="shrink-0"
          >
            <path
              fill="#039be5"
              d="M24 5A19 19 0 1 0 24 43A19 19 0 1 0 24 5Z"
            ></path>
            <path
              fill="#fff"
              d="M26.572,29.036h4.917l0.772-4.995h-5.69v-2.73c0-2.075,0.678-3.915,2.619-3.915h3.119v-4.359c-0.548-0.074-1.707-0.236-3.897-0.236c-4.573,0-7.254,2.415-7.254,7.917v3.323h-4.701v4.995h4.701v13.729C22.089,42.905,23.032,43,24,43c0.875,0,1.729-0.08,2.572-0.194V29.036z"
            ></path>
          </svg>
        }
      />

      <Row
        url="https://form.jotform.com/241713574736461"
        title="Got some time to share your thoughts?"
        icon={<MessageSquare size={20} className="shrink-0" />}
      />

      <Row
        url="https://www.facebook.com/groups/519574620423944"
        title="Join our facebook group for more updates"
        icon={<UsersRound size={20} className="shrink-0" />}
      />
    </>
  );
}
