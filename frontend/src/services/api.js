import axios from 'axios';

// Determine API base URL based on environment
// In production (Docker), nginx proxies /api to backend
// In development, connect directly to localhost:8000
const API_BASE_URL = import.meta.env.PROD
  ? '/api/v1'  // Production: use nginx proxy
  : 'http://localhost:8000/api/v1';  // Development: direct connection

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health endpoints
export const checkHealth = () => api.get('/health');
export const checkProxmoxStatus = () => api.get('/proxmox/status');

// Template endpoints
export const listTemplates = () => api.get('/templates');
export const getTemplateDetails = (vmid) => api.get(`/templates/${vmid}`);
export const cloneTemplate = (data) => api.post('/templates/clone', data);
export const batchCloneTemplate = (data) => api.post('/templates/batch-clone', data);
export const validateTemplate = (vmid) => api.get(`/templates/${vmid}/validate`);

// VM endpoints
export const createVM = (data) => api.post('/vms/create', data);
export const batchCreateVM = (data) => api.post('/vms/batch-create', data);
export const getVMInfo = (vmid) => api.get(`/vms/${vmid}`);
export const getVMStatus = (vmid) => api.get(`/vms/${vmid}/status`);
export const validateVM = (vmid, osType = 'linux') =>
  api.post(`/vms/${vmid}/validate?os_type=${osType}`);

// Resource endpoints
export const listStorages = () => api.get('/resources/storages');
export const listISOImages = () => api.get('/resources/iso-images');
export const listNetworkBridges = () => api.get('/resources/network-bridges');
export const getAllResources = () => api.get('/resources/all');

export default api;
