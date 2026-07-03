/** @type {import('next').NextConfig} */
module.exports = {
    output: 'export',
    env: {
        BASE_API_URL: process.env.BASE_API_URL || 'https://indian-visa-status-595946522239.asia-southeast1.run.app',
    },
    images: { unoptimized: true },
};
