import { Link } from 'react-router-dom'

export default function About() {
  return (
    <div className="w-full max-w-2xl">
      <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-4">About</h1>
      <div className="prose prose-gray dark:prose-invert max-w-none space-y-4 text-gray-600 dark:text-gray-300">
        <p>
          A minimal URL shortener that creates compact links from long URLs. Built with React and
          deployed on AWS.
        </p>
        <h2 className="text-lg font-medium text-gray-800 dark:text-gray-100 mt-6">Features</h2>
        <ul className="list-disc list-inside space-y-1">
          <li>Shorten long URLs</li>
          <li>Optional custom alias for memorable links</li>
          <li>Optional expiry date for temporary links</li>
          <li>Dark and light mode</li>
        </ul>
        <h2 className="text-lg font-medium text-gray-800 dark:text-gray-100 mt-6">Tech Stack</h2>
        <ul className="list-disc list-inside space-y-1">
          <li>Frontend: React, Vite, Tailwind CSS</li>
          <li>Backend: AWS API Gateway, Lambda, DynamoDB</li>
          <li>Hosting: S3, CloudFront</li>
        </ul>
        <Link
          to="/"
          className="inline-block mt-6 text-teal-600 dark:text-teal-400 font-medium hover:underline"
        >
          ← Back to shorten
        </Link>
      </div>
    </div>
  )
}
