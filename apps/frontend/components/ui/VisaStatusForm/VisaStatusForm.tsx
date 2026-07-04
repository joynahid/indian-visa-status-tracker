'use client';

import { useForm } from 'react-hook-form';
import axios from 'axios';
import { useMutation } from '@tanstack/react-query';
import { joiResolver } from '@hookform/resolvers/joi';
import Button from '../Button';
import Joi from 'joi';
import { Check, CheckCircle2, Copy, CopyCheck, RefreshCcw } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Slide, toast } from 'react-toastify';
import copy from 'clipboard-copy';

const mockResponse = {result: [
  {
    applicant_name: 'MD NAHID HASAN',
    passtrack: {
      Process: {
        '0': 'Received At Center',
        '1': 'Sent To HCI',
        '2': 'Ready For Delivery',
        '3': 'Delivered From Center On 2024-05-00'
      },
      Status: {
        '0': 'Done',
        '1': 'Done',
        '2': 'Done',
        '3': 'Done'
      }
    },
    url: 'https://www.passtrack.net/regular_passport.php',
    status_text: null
  },
  {
    applicant_name: null,
    passtrack: null,
    url: 'https://indianvisa-bangladesh.nic.in/visa/StatusEnquiry',
    status_text: '    Application Status :- Under Process'
  },
  {
    applicant_name: null,
    passtrack: null,
    url: 'https://indianvisaonline.gov.in/visa/StatusEnquiry',
    status_text:
      'Your visa is Processed and Printed.\nIf not collected earlier,Please contact the respective office on next working day where you have submitted your Application.'
  }
]};

interface VisaStatusInput {
  application_id: string;
  passport_number: string;
}

const VisaStatusInputSchema = Joi.object({
  application_id: Joi.string()
    .required()
    .regex(/^[A-Z0-9]+$/)
    .length(12)
    .messages({
      'string.pattern.base': 'Application id must be capital letters and numbers',
      'any.required': 'Application id is required',
      'string.empty': 'Application id can\'t be empty',
      'string.regex.base': 'Application id must be capital letters and numbers',
      'string.length': 'Application id must be 12 characters'
    }),
  passport_number: Joi.string().required().regex(/^[A-Z0-9]+$/).messages({
    'any.required': 'Passport number is required',
    'string.empty': 'Passport number can\'t be empty',
    'string.pattern.base': 'Passport number must be capital letters and numbers',
  })
});

const inpClass = 'w-full border dark:border-zinc-600 border-slate-300 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 p-2 rounded-md my-2';

export function VisaStatusForm() {
  const apiBaseUrl = process.env.BASE_API_URL;

  const {
    handleSubmit,
    reset,
    register,
    formState: { errors }
  } = useForm<VisaStatusInput>({
    resolver: joiResolver(VisaStatusInputSchema)
  });

  const [currentTimer, setCurrentTimer] = useState<any>(null);
  const [time, setTime] = useState(0);

  const [copied, setCopied] = useState(false);

  const visaStatus = useMutation({
    mutationKey: ['get-visa-status'],
    mutationFn: async (data: VisaStatusInput) => {
      const response = await axios.post(apiBaseUrl + '/track/start', data);
      return response.data;
    },
    onSuccess: (data) => {
      // Redirect to the status page (query param) which will poll for results
      if (data?.slug) {
        window.location.href = '/?slug=' + data.slug;
      }
    },
    onError: (error, payload, context) => {
      ``
      toast.error(error.message, {
        transition: Slide,
        autoClose: 3000,
        position: 'bottom-center',
        hideProgressBar: true,
        theme: 'dark'
      });

      if(typeof (error as any)?.response?.data?.detail === 'string') {
        toast.error((error as any)?.response?.data?.detail, {
          transition: Slide,
          autoClose: 3000,
          position: 'bottom-center',
          hideProgressBar: true,
          theme: 'dark'
        });
      }
    }
  });

  useEffect(() => {
    let timeout: any = null;
    if (copied) {
      timeout = setTimeout(() => {
        setCopied(false);
      }, 3000);
    }

    return () => {
      if (timeout) {
        clearTimeout(timeout);
      }
    };
  }, [copied]);

  useEffect(() => {
    if (visaStatus.isIdle && currentTimer) {
      clearInterval(currentTimer);
      setCurrentTimer(null);
    }
  }, [visaStatus]);

  const onSubmit = async (data: VisaStatusInput) => {
    visaStatus.mutate(data);
    setTime(0);

    if (currentTimer !== null) {
      clearInterval(currentTimer);
      setCurrentTimer(null);
    }

    setCurrentTimer(
      setInterval(() => {
        setTime((time) => time + 1);
      }, 1000)
    );
  };

  return (
    <div className="text-zinc-500">
      {!visaStatus.isSuccess && (
        <form onSubmit={handleSubmit(onSubmit)}>
          <input
            type="text"
            disabled={visaStatus.isSuccess || visaStatus.isPending}
            placeholder="Enter your application id"
            className={inpClass}
            {...register('application_id')}
          />
          <p className="text-red-500">{errors.application_id?.message}</p>

          <input
            type="text"
            disabled={visaStatus.isSuccess || visaStatus.isPending}
            placeholder="Enter your passport number"
            className={inpClass}
            {...register('passport_number')}
          />

          <p className="text-red-500">{errors.passport_number?.message}</p>

          {!visaStatus.isSuccess ? (
            <div>
              {visaStatus.isError && (
                <div className="text-red-500">
                  { typeof (visaStatus.error as any).response?.data?.detail !== 'string' && (visaStatus.error as any)?.response?.data?.detail?.map(
                    (item: any, idx: number) => (
                      <p key={idx}>
                        {item.loc[1]}: {item.msg}
                      </p>
                    )
                  )}
                </div>
              )}
              <Button
                disabled={visaStatus.isPending}
                loading={visaStatus.isPending}
                type="submit"
                className="w p-3 rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-black my-2"
              >
                Submit
              </Button>

              {visaStatus.isPending && (
                <p className="dark:text-zinc-400 text-zinc-600 text-sm animate-pulse">
                  Please wait (
                  {time} seconds)...
                </p>
              )}
            </div>
          ) : null}

          {/* Show json response */}
        </form>
      )}

      {visaStatus.isSuccess && (
        // space between two divs
        <div className="flex justify-between">
          <div className="rounded-md text-zinc-200 my-2">
            <a
              href="#"
              onClick={() => {
                visaStatus.reset();
              }}
              className=""
            >
              <div className="flex items-center gap-2 dark:text-white text-black hover:text-zinc-900">
                <RefreshCcw /> Check another one
              </div>
            </a>
          </div>

          <div className="rounded-md text-zinc-200 my-2">
            <a
              href="#"
              onClick={() => {
                copy(location.host + '/' + visaStatus.data.slug)
                setCopied(true);
              }}
              className="animate-fade"
            >
              <div className="flex items-center gap-2 flex items-center gap-2 dark:text-white text-black hover:text-zinc-900">
                {copied ? <CopyCheck /> : <Copy />}{' '}
                {copied ? 'Copied!' : 'Copy Link'}
              </div>
            </a>
          </div>
        </div>
      )}

      {visaStatus.isSuccess && <StatusList data={visaStatus.data} />}
    </div>
  );
}

// Component to render each row of the process/status table
const ProcessRow = ({ process, status }: any) => {
  const cls = status == 'Done' ? ' dark:text-white text-zinc-800 dark:bg-zinc-800' : '';

  return (
    <tr className="border dark:border-zinc-700 border-zinc-300">
      <td className={'py-1 px-2' + cls}>{process}</td>
      <td className="py-1 px-2 dark:text-zinc-300 font-semibold">{status == 'Done' ? <Check color='green' /> : status}</td>
    </tr>
  );
};

// Component to render the process/status table
const ProcessTable = ({ processes }: any) => {
  return (
    <table className="w-full mb-2 border dark:border-zinc-700 border-zinc-300">
      <tbody>
        {processes.map((process: any, index: any) => (
          <ProcessRow
            key={index}
            process={process.process}
            status={process.status}
          />
        ))}
      </tbody>
    </table>
  );
};

// Component to render each applicant's card
const StatusCard = ({ applicant }: any) => {
  return (
    <div className="rounded-md p-2">
      {applicant.applicant_name && (
        <h1 className="text-lg text-zinc-900 dark:text-white font-semibold pb-2">
          {applicant.applicant_name}
        </h1>
      )}

      {applicant.passtrack?.Process ? (
        <div>
          <ProcessTable
            processes={Object.keys(applicant.passtrack.Process).map((key) => ({
              process: applicant.passtrack.Process[key],
              status: applicant.passtrack.Status[key]
            }))}
          />
        </div>
      ) : (
        <div className="gap-2">
          <p
            className="text-xl text-zinc-800 dark:text-zinc-200"
            dangerouslySetInnerHTML={{
              __html: applicant?.status_text?.replace(/\n/g, '<br>')
            }}
          ></p>
        </div>
      )}

      {applicant?.url && (
        <p className="dark:text-zinc-400 text-zinc-500 text-xs my-2">
          From &nbsp;
          <a
            href={applicant.url}
            target="_blank"
            rel="noopener noreferrer"
            className="dark:text-zinc-400 text-zinc-500 hover:underline"
          >
            {applicant.url}
          </a>
        </p>
      )}
    </div>
  );
};

const StatusList = (props: any) => {
  const { data } = props;

  return (
    <div>
      <div className="my-4 grid border dark:border-zinc-700 border-slate-300 p-2 rounded-md">
        <p className="p-2 text-sm">
        <span className="text-gray-400">
          Time taken:{' '}
          </span>
          <span className="text-gray-800 dark:text-white">
            {data.processing_time_seconds != null
              ? Math.round((data.processing_time_seconds + Number.EPSILON) * 100) / 100
              : '0'}{' '}
            seconds
          </span>
        </p>
        {data?.result?.map((applicant: any, index: any) => (
          <StatusCard key={index} applicant={applicant} />
        ))}
      </div>
    </div>
  );
};

export default StatusList;
