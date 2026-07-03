import React from 'react';

const PrivacyPolicy: React.FC = () => {
  return (
    // line height 1.8
    <div className="max-w-6xl px-6 mx-auto m-auto my-8 border rounded-md p border-zinc-700 prose dark:text-white text-zinc-800">
      <div className="prose">
        <h1 className='text-2xl py-2'>Privacy Policy</h1>
        <p>
          <strong>Effective Date:</strong> 19 June, 2024
        </p>

        <h2 className='text-xl py-2'>Introduction</h2>
        <p>
          Welcome to easyindianvisa.info. We are committed to safeguarding your
          privacy and ensuring that your personal information is protected. This
          Privacy Policy outlines how we collect, use, and protect your data
          when you use our website to track your Indian visa application.
        </p>

        <h2 className='text-xl py-2'>Information We Collect</h2>
        <p>
          When you use our website to track your visa application, we collect
          the following information:
        </p>
        <ul>
          <li>
            <strong>Application ID:</strong> Your unique visa application
            identifier.
          </li>
          <li>
            <strong>Passport Information:</strong> Necessary details from your
            passport to track your visa status.
          </li>
          <li>
            <strong>Visa Status:</strong> The current status of your visa
            application.
          </li>
        </ul>

        <h2 className='text-xl py-2'>How We Use Your Information</h2>
        <p>We use the information we collect for the following purposes:</p>
        <ul>
          <li>
            <strong>Tracking Visa Applications:</strong> To provide you with
            up-to-date information on your visa application status.
          </li>
          <li>
            <strong>Sharing Feature:</strong> To allow you to share your
            application status with others as requested.
          </li>
        </ul>

        <h2 className='text-xl py-2'>Data Storage and Security</h2>
        <p>
          We take data security seriously and implement various measures to
          protect your information:
        </p>
        <ul>
          <li>
            <strong>Data Storage:</strong> Your information is stored in secure
            databases.
          </li>
          <li>
            <strong>Data Security:</strong> We use encryption and other security
            protocols to safeguard your data from unauthorized access.
          </li>
        </ul>

        <h2 className='text-xl py-2'>Data Deletion</h2>
        <p>
          If you wish to delete your data, please send an email to{' '}
          <a href="mailto:hello@easyindianvisa.com">
            hello@easyindianvisa.com
          </a>{' '}
          with your request. We will delete your information from our database
          within a reasonable timeframe.
        </p>

        <h2 className='text-xl py-2'>Changes to This Privacy Policy</h2>
        <p>
          We may update this Privacy Policy from time to time. Any changes will
          be posted on this page with an updated effective date.
        </p>

        <h2 className='text-xl py-2'>Contact Us</h2>
        <p>
          If you have any questions or concerns about our Privacy Policy, please
          contact us at{' '}
          <a href="mailto:hello@easyindianvisa.com">
            hello@easyindianvisa.com
          </a>
          .
        </p>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
