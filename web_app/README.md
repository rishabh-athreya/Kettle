# Kettle AI Web Dashboard

A modern, responsive web dashboard for the Kettle AI project automation tool. Built with Next.js, TypeScript, and Tailwind CSS.

## Features

- **Real-time Task History**: View all tasks extracted from Slack messages
- **Approval System**: Approve or reject tasks like Cursor's interface
- **Message Context**: See the original Slack messages that triggered tasks
- **Live Updates**: Automatic polling for real-time data updates
- **Modern UI**: Beautiful dark theme with smooth animations
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Frontend**: Next.js 14, React 18, TypeScript
- **Styling**: Tailwind CSS, Framer Motion
- **Icons**: Lucide React
- **Backend**: Flask API (separate service)
- **Deployment**: Vercel

## Quick Start

### 1. Install Dependencies

```bash
cd web_app
npm install
```

### 2. Start the Development Server

```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### 3. Start the API Backend

In a separate terminal, start the Flask API:

```bash
cd web_app/api
pip install -r requirements.txt
python app.py
```

The API will be available at `http://localhost:5001`

## Project Structure

```
web_app/
├── app/                    # Next.js app directory
│   ├── components/         # React components
│   │   ├── TaskCard.tsx    # Individual task display
│   │   ├── MessageCard.tsx # Slack message display
│   │   └── StatsCard.tsx   # Statistics cards
│   ├── globals.css         # Global styles
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Main dashboard page
│   └── types.ts            # TypeScript definitions
├── api/                    # Flask backend
│   ├── app.py              # API server
│   └── requirements.txt    # Python dependencies
├── package.json            # Node.js dependencies
├── tailwind.config.js      # Tailwind configuration
├── next.config.js          # Next.js configuration
├── vercel.json             # Vercel deployment config
└── README.md               # This file
```

## API Endpoints

The Flask backend provides the following endpoints:

- `GET /api/tasks` - Get all tasks
- `POST /api/tasks/{id}/approve` - Approve/reject a task
- `GET /api/messages` - Get all Slack messages
- `GET /api/stats` - Get dashboard statistics
- `GET /api/health` - Health check

## Deployment

### Deploy to Vercel

1. **Connect to Vercel**:
   ```bash
   npm install -g vercel
   vercel login
   ```

2. **Deploy**:
   ```bash
   vercel --prod
   ```

3. **Set Environment Variables** (if needed):
   - Go to your Vercel dashboard
   - Navigate to your project settings
   - Add any required environment variables

### Deploy API Backend

The Flask API can be deployed to:
- **Railway**: Easy deployment with automatic scaling
- **Render**: Free tier available
- **Heroku**: Traditional deployment option
- **Vercel Functions**: Serverless functions (requires adaptation)

## Configuration

### API URL Configuration

Update the API base URL in `next.config.js` for production:

```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'https://your-api-domain.com/api/:path*',
    },
  ]
}
```

### Data Source

The dashboard reads from the Kettle JSON files:
- `json/phased_tasks.json` - Task data
- `json/messages.json` - Slack messages

Make sure these files are accessible to your API backend.

## Development

### Adding New Components

1. Create a new component in `app/components/`
2. Export it as the default export
3. Import and use it in your pages

### Styling

- Use Tailwind CSS classes for styling
- Custom CSS variables are defined in `globals.css`
- Component-specific styles use the `@layer components` directive

### TypeScript

- All components are typed with TypeScript
- Types are defined in `app/types.ts`
- Use strict TypeScript checking

## Troubleshooting

### Common Issues

1. **API Connection Errors**:
   - Check that the Flask API is running on port 5001
   - Verify the API URL in `next.config.js`
   - Check CORS settings

2. **Port Conflicts**:
   - The API uses port 5001 to avoid conflicts with macOS AirPlay Receiver
   - If you need to change the port, update both `api/app.py` and `next.config.js`

3. **Build Errors**:
   - Run `npm install` to ensure all dependencies are installed
   - Check TypeScript errors with `npm run lint`

4. **Data Not Loading**:
   - Verify the JSON files exist in the Kettle directory
   - Check API endpoint responses
   - Review browser console for errors

### Performance

- The dashboard polls for updates every 5 seconds
- Consider implementing WebSockets for real-time updates
- Optimize images and assets for faster loading

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Feel free to contribute and improve the dashboard! 