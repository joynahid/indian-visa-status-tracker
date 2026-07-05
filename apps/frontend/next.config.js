/** @type {import('next').NextConfig} */
module.exports = {
    output: 'export',
    env: {
        BASE_API_URL: process.env.BASE_API_URL || 'http://localhost:8765',
    },
    images: { unoptimized: true },
};
