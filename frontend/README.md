# Proxmox VM Deployer - Frontend

React frontend application for deploying VMs on Proxmox.

## Features

- **Dark Theme**: Modern dark UI with Tailwind CSS
- **Template Cloning**: Deploy VMs from templates with custom resources
- **VM Creation**: Create new VMs from scratch
- **Real-time Status**: Connection status and deployment feedback
- **Helper Tooltips**: Contextual help for all form fields
- **Post-Deployment Validation**: Automated health checks

## Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The application will be available at: **http://localhost:3001**

## Build for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Header.jsx              # App header
│   │   ├── TabButton.jsx           # Tab navigation
│   │   ├── FormInput.jsx           # Input with helper
│   │   ├── FormSelect.jsx          # Select with helper
│   │   ├── FormCheckbox.jsx        # Checkbox component
│   │   ├── TemplateCloneForm.jsx   # Template cloning (PRIORITY)
│   │   ├── VMCreateForm.jsx        # VM creation
│   │   └── DeploymentStatus.jsx    # Success/validation display
│   │
│   ├── services/
│   │   └── api.js                  # Backend API client
│   │
│   ├── App.jsx                     # Main app component
│   ├── main.jsx                    # App entry point
│   └── index.css                   # Global styles + Tailwind
│
├── index.html                      # HTML template
├── package.json                    # Dependencies
├── vite.config.js                  # Vite configuration
└── tailwind.config.js              # Tailwind configuration
```

## Usage

### Clone from Template (Recommended)

1. Select a template from the dropdown
2. Enter a name for your new VM
3. Customize CPU cores and memory if needed
4. Choose clone options:
   - **Full Clone**: Independent copy (recommended)
   - **Start After Clone**: Auto-start the VM
5. Click "Clone Template"
6. Optionally run post-deployment validation

### Create New VM

1. Enter VM name
2. Select OS type (Linux/Windows)
3. Configure resources (CPU, memory, disk)
4. Click "Create VM"
5. Note: You'll need to install an OS via ISO

## API Integration

The frontend connects to the backend API at `http://localhost:8000/api/v1`.

API endpoints used:
- `GET /health` - API health check
- `GET /proxmox/status` - Proxmox connection status
- `GET /templates` - List templates
- `POST /templates/clone` - Clone template
- `POST /vms/create` - Create VM
- `POST /vms/{vmid}/validate` - Validate deployment

## Development

### Available Scripts

- `npm run dev` - Start development server (port 3001)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Styling

- **Framework**: Tailwind CSS
- **Icons**: Heroicons (React)
- **Theme**: Custom dark theme with blue accents

### Color Palette

- Background: `#0f172a`
- Surface: `#1e293b`
- Border: `#334155`
- Text: `#e2e8f0`
- Muted: `#94a3b8`
- Primary: Blue (`#3b82f6`)

## Troubleshooting

### Backend Connection Failed

- Ensure backend API is running on port 8000
- Check CORS settings in backend `.env`
- Verify `CORS_ORIGINS=http://localhost:3001`

### Templates Not Loading

- Check Proxmox connection in backend
- Ensure templates exist and are marked as templates in Proxmox
- Check browser console for API errors

### Validation Fails

- Ensure QEMU guest agent is installed in VMs
- Check that VMs can obtain IP addresses
- Verify firewall rules allow SSH (port 22) or RDP (port 3389)

## Technologies

- **React 18.3**: UI framework
- **Vite 5.4**: Build tool and dev server
- **Tailwind CSS 3.4**: Utility-first CSS
- **Heroicons 2.2**: Icon library
- **Axios 1.7**: HTTP client

## License

Part of the Proxmox VM Deployer project.
