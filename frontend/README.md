This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

### Installation

**Important:** First, install the dependencies before running the development server:

```bash
npm install
```

### Configuration AWS Amplify (email / mot de passe)

Create a `.env.local` file in the root directory with the following variables:

```env
NEXT_PUBLIC_AWS_REGION=eu-west-3
NEXT_PUBLIC_AWS_USER_POOL_ID=your-user-pool-id
NEXT_PUBLIC_AWS_CLIENT_ID=your-client-id
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000
NEXT_PUBLIC_TURNSTILE_SITE_KEY=your-turnstile-site-key
```

### Running the development server

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Pages Available

The following pages are available:

- `/` - Home page
- `/connexion` - Login page
- `/inscription` - Sign up page
- `/confirmation` - Email confirmation page (requires `email` query parameter)
- `/contact` - Contact page with form and Turnstile captcha
- `/mon-compte` - User account page (requires authentication)

### Authentication Pages

All authentication pages support:
- Email/password authentication via AWS Cognito
- Google OAuth authentication
- Password visibility toggle
- Error handling with French translations
- Responsive design

### Contact Page

The contact page (`/contact`) includes:
- Contact form with validation
- Cloudflare Turnstile invisible captcha
- FAQ section
- Responsive design matching the template style

## Project Structure

- `src/app/` - Next.js App Router pages
- `src/components/` - React components
- `src/config/` - Configuration files (AWS Amplify)
- `src/utils/` - Utility functions (logger, toast notifications)

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
