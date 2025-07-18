# Medical Vector Database Dashboard

A modern React dashboard for the Medical Vector Database OCR/NER system. This frontend provides a comprehensive interface for uploading, searching, and analyzing medical documents.

## Features

### 🎯 Core Features
- **Document Upload**: Drag-and-drop file upload with progress tracking
- **Advanced Search**: Semantic search with entity filtering and confidence scoring
- **Document Management**: View, delete, and manage all uploaded documents
- **Real-time Analytics**: Charts and statistics for processing insights
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### 📊 Dashboard
- System health monitoring
- Processing statistics
- Entity distribution charts
- Recent upload activity
- Success rate tracking

### 🔍 Search Capabilities
- Semantic document search
- Entity-based filtering
- Confidence score display
- Highlighted search results
- Advanced search options

### 📁 Document Management
- Data grid with sorting and filtering
- Document details view
- Entity extraction display
- OCR confidence indicators
- Bulk operations support

### 📈 Analytics
- Processing statistics charts
- Entity distribution analysis
- System performance metrics
- Trend visualization

## Technology Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Material-UI (MUI)** - Professional UI components
- **React Query** - Server state management
- **React Router** - Client-side routing
- **Recharts** - Data visualization
- **React Dropzone** - File upload handling
- **Vite** - Fast build tool
- **Axios** - HTTP client

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

3. **Open in browser:**
   ```
   http://localhost:3000
   ```

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   └── Layout.tsx      # Main layout with navigation
│   ├── pages/              # Page components
│   │   ├── Dashboard.tsx   # Main dashboard
│   │   ├── Upload.tsx      # Document upload
│   │   ├── Search.tsx      # Search interface
│   │   ├── Documents.tsx   # Document management
│   │   ├── Analytics.tsx   # Analytics and charts
│   │   └── Settings.tsx    # System settings
│   ├── services/           # API services
│   │   └── api.ts         # API client
│   ├── types/              # TypeScript type definitions
│   │   └── index.ts       # API response types
│   ├── App.tsx            # Main app component
│   └── main.tsx           # App entry point
├── public/                 # Static assets
├── package.json           # Dependencies and scripts
├── vite.config.ts         # Vite configuration
└── tsconfig.json         # TypeScript configuration
```

## API Integration

The frontend communicates with the backend API through the `apiService` in `src/services/api.ts`. Key endpoints:

- `GET /api/v1/health` - System health check
- `POST /api/v1/upload` - Document upload
- `GET /api/v1/search` - Document search
- `GET /api/v1/documents` - List documents
- `GET /api/v1/stats` - System statistics

## Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=Medical Vector Database
```

### Vite Configuration

The Vite config (`vite.config.ts`) includes:
- React plugin
- API proxy to backend
- Path aliases for clean imports
- Development server settings

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Code Style

- TypeScript for type safety
- Material-UI components for consistency
- React Query for server state
- Functional components with hooks

## Features in Detail

### Document Upload
- Drag-and-drop interface
- Multiple file support
- Progress tracking
- File validation
- Metadata input
- Error handling

### Search Interface
- Real-time search
- Entity filtering
- Confidence scoring
- Result highlighting
- Advanced options

### Document Management
- Data grid with pagination
- Sorting and filtering
- Bulk operations
- Document details view
- Entity extraction display

### Analytics Dashboard
- Processing statistics
- Entity distribution
- System health
- Performance metrics
- Interactive charts

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Medical Vector Database system.

## Support

For issues and questions:
1. Check the backend API is running
2. Verify API endpoints are accessible
3. Check browser console for errors
4. Review network requests in DevTools 