import { useState, useEffect } from 'react'
import { PlusCircleIcon, ChevronDownIcon, ChevronUpIcon, TrashIcon, CheckCircleIcon } from '@heroicons/react/24/solid'
import { batchCreateVM, listISOImages, listStorages, listNetworkBridges } from '../services/api'
import FormInput from './FormInput'
import FormSelect from './FormSelect'
import FormCheckbox from './FormCheckbox'
import TagInput from './TagInput'
import DeploymentStatus from './DeploymentStatus'

export default function VMCreateForm({ disabled }) {
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  // Resources
  const [isoImages, setIsoImages] = useState([])
  const [storages, setStorages] = useState([])
  const [networkBridges, setNetworkBridges] = useState([])
  const [loadingResources, setLoadingResources] = useState(true)

  // Section expansion state
  const [expandedSections, setExpandedSections] = useState({
    general: true,
    os: true,
    system: false,
    disks: true,
    cpu: true,
    memory: true,
    network: true,
    tags: true
  })

  // Array of VMs to create
  const [vmsToCreate, setVmsToCreate] = useState([{
    // General
    name: '',
    vmid: '',

    // OS
    iso: '',
    virtio_iso: '',
    os_type: 'linux',

    // System
    bios: 'seabios',
    machine: 'q35',
    cpu_type: 'host',

    // Disks
    storage: '',
    disk_size: 32,
    disk_format: 'raw',

    // CPU
    cores: 2,
    sockets: 1,

    // Memory
    memory: 4096,

    // Network
    network_bridge: '',
    network_model: 'virtio',

    // Tags
    tags: [],

    // Options
    start_on_creation: false,
    enable_guest_agent: false
  }])

  const [currentVMIndex, setCurrentVMIndex] = useState(0)

  useEffect(() => {
    loadResources()
  }, [])

  // Apply Windows best practices when OS type changes to Windows
  useEffect(() => {
    const currentVM = vmsToCreate[currentVMIndex]
    if (currentVM.os_type === 'windows') {
      // Apply Windows best practices automatically
      const updatedVMs = [...vmsToCreate]
      updatedVMs[currentVMIndex] = {
        ...updatedVMs[currentVMIndex],
        bios: 'ovmf',           // UEFI required for Windows 11, recommended for Windows Server 2022
        machine: 'q35',         // Modern machine type
        network_model: 'virtio' // Already set, but ensure it's VirtIO
      }
      setVmsToCreate(updatedVMs)
    }
  }, [vmsToCreate[currentVMIndex]?.os_type])

  const loadResources = async () => {
    try {
      const [isoResp, storageResp, networkResp] = await Promise.all([
        listISOImages(),
        listStorages(),
        listNetworkBridges()
      ])

      setIsoImages(isoResp.data || [])
      setStorages(storageResp.data || [])
      setNetworkBridges(networkResp.data || [])

      // Set defaults if available
      if (storageResp.data && storageResp.data.length > 0) {
        const defaultStorage = storageResp.data[0].storage
        setVmsToCreate(prev => prev.map(vm => ({ ...vm, storage: defaultStorage })))
      }
      if (networkResp.data && networkResp.data.length > 0) {
        const defaultBridge = networkResp.data[0].iface
        setVmsToCreate(prev => prev.map(vm => ({ ...vm, network_bridge: defaultBridge })))
      }
    } catch (err) {
      console.error('Failed to load resources:', err)
      setError('Failed to load resources from Proxmox')
    } finally {
      setLoadingResources(false)
    }
  }

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target
    const updatedVMs = [...vmsToCreate]
    updatedVMs[currentVMIndex] = {
      ...updatedVMs[currentVMIndex],
      [name]: type === 'checkbox' ? checked : value
    }
    setVmsToCreate(updatedVMs)
  }

  const handleTagsChange = (newTags) => {
    const updatedVMs = [...vmsToCreate]
    updatedVMs[currentVMIndex] = { ...updatedVMs[currentVMIndex], tags: newTags }
    setVmsToCreate(updatedVMs)
  }

  const addVM = () => {
    // Copy current VM data but clear name and vmid
    const lastVM = vmsToCreate[vmsToCreate.length - 1]
    const newVM = {
      ...lastVM,
      name: '',
      vmid: '',
      tags: [] // Also clear tags for new VM
    }
    setVmsToCreate([...vmsToCreate, newVM])
    setCurrentVMIndex(vmsToCreate.length)
  }

  const removeVM = (index) => {
    if (vmsToCreate.length === 1) return // Don't remove if only one
    const updatedVMs = vmsToCreate.filter((_, i) => i !== index)
    setVmsToCreate(updatedVMs)
    // Adjust current index if needed
    if (currentVMIndex >= updatedVMs.length) {
      setCurrentVMIndex(updatedVMs.length - 1)
    }
  }

  const selectVM = (index) => {
    setCurrentVMIndex(index)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    setResult(null)

    try {
      // Prepare all VMs for submission
      const payload = vmsToCreate.map(vm => ({
        name: vm.name,
        vmid: vm.vmid ? parseInt(vm.vmid) : undefined,
        cores: parseInt(vm.cores),
        sockets: parseInt(vm.sockets),
        memory: parseInt(vm.memory),
        disk_size: parseInt(vm.disk_size),
        storage: vm.storage,
        network_bridge: vm.network_bridge,
        network_model: vm.network_model,
        os_type: vm.os_type,
        bios: vm.bios,
        machine: vm.machine,
        cpu_type: vm.cpu_type,
        iso: vm.iso || undefined,
        virtio_iso: vm.virtio_iso || undefined,
        tags: vm.tags.length > 0 ? vm.tags : undefined,
        start_on_creation: vm.start_on_creation,
        enable_guest_agent: vm.enable_guest_agent
      }))

      const response = await batchCreateVM(payload)
      setResult(response.data)

      // Reset form on success
      setVmsToCreate([{
        name: '',
        vmid: '',
        iso: '',
        virtio_iso: '',
        os_type: 'linux',
        bios: 'seabios',
        machine: 'q35',
        cpu_type: 'host',
        storage: storages[0]?.storage || '',
        disk_size: 32,
        disk_format: 'raw',
        cores: 2,
        sockets: 1,
        memory: 4096,
        network_bridge: networkBridges[0]?.iface || '',
        network_model: 'virtio',
        tags: [],
        start_on_creation: false,
        enable_guest_agent: false
      }])
      setCurrentVMIndex(0)
    } catch (err) {
      console.error('VM creation failed:', err)
      setError(err.response?.data?.detail || 'Failed to create VM(s)')
    } finally {
      setSubmitting(false)
    }
  }

  const SectionHeader = ({ title, section, icon: Icon }) => (
    <button
      type="button"
      onClick={() => toggleSection(section)}
      className="w-full flex items-center justify-between px-4 py-3 bg-dark-bg rounded-t-lg hover:bg-opacity-80 transition-colors"
    >
      <div className="flex items-center">
        <Icon className="h-5 w-5 text-blue-500 mr-2" />
        <span className="font-medium text-dark-text">{title}</span>
      </div>
      {expandedSections[section] ? (
        <ChevronUpIcon className="h-5 w-5 text-dark-muted" />
      ) : (
        <ChevronDownIcon className="h-5 w-5 text-dark-muted" />
      )}
    </button>
  )

  return (
    <div className="bg-dark-surface rounded-lg shadow-lg border border-dark-border">
      <div className="px-6 py-4 border-b border-dark-border">
        <h2 className="text-xl font-semibold text-dark-text flex items-center">
          <PlusCircleIcon className="h-6 w-6 text-blue-500 mr-2" />
          Create New VM
        </h2>
        <p className="text-dark-muted text-sm mt-1">
          Configure a new virtual machine with full control over all settings
        </p>
      </div>

      {loadingResources ? (
        <div className="p-6 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-3 text-dark-muted">Loading resources...</span>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="p-6 space-y-4">

          {/* VM List */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="block text-sm font-medium text-dark-text">
                VMs to Create ({vmsToCreate.length})
              </label>
              <button
                type="button"
                onClick={addVM}
                disabled={disabled}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <PlusCircleIcon className="h-4 w-4" />
                Add Another VM
              </button>
            </div>

            <div className="flex gap-2 flex-wrap mb-6">
              {vmsToCreate.map((vm, index) => (
                <div
                  key={index}
                  onClick={() => selectVM(index)}
                  className={`
                    relative flex items-center gap-2 px-4 py-2 rounded-lg cursor-pointer transition-all
                    ${currentVMIndex === index
                      ? 'bg-blue-900/40 border-2 border-blue-500 ring-2 ring-blue-500/20'
                      : 'bg-dark-bg border-2 border-dark-border hover:border-blue-700'
                    }
                  `}
                >
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-dark-text">
                      VM {index + 1}
                    </span>
                    {vm.name && (
                      <span className="text-xs text-dark-muted">{vm.name}</span>
                    )}
                  </div>

                  {vmsToCreate.length > 1 && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        removeVM(index)
                      }}
                      className="ml-2 text-red-400 hover:text-red-300"
                      title="Remove this VM"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>

            <h3 className="text-lg font-medium text-dark-text mb-4 border-t border-dark-border pt-4">
              Configure VM {currentVMIndex + 1}
            </h3>
          </div>

          {/* General Section */}
          <div className="border border-dark-border rounded-lg overflow-hidden">
            <SectionHeader title="General" section="general" icon={PlusCircleIcon} />
            {expandedSections.general && (
              <div className="p-4 space-y-4">
                <FormInput
                  label="VM ID"
                  name="vmid"
                  type="number"
                  value={vmsToCreate[currentVMIndex].vmid}
                  onChange={handleInputChange}
                  placeholder="Leave empty for auto-assignment"
                  helper="Unique VM ID (100-999999). Leave empty to auto-assign."
                  disabled={disabled}
                />
                <FormInput
                  label="VM Name"
                  name="name"
                  value={vmsToCreate[currentVMIndex].name}
                  onChange={handleInputChange}
                  placeholder="e.g., production-web-01"
                  required
                  helper="Unique name for your VM. Use lowercase, numbers, and hyphens."
                  disabled={disabled}
                />
              </div>
            )}
          </div>

          {/* OS Section */}
          <div className="border border-dark-border rounded-lg overflow-hidden">
            <SectionHeader title="OS" section="os" icon={PlusCircleIcon} />
            {expandedSections.os && (
              <div className="p-4 space-y-4">
                <FormSelect
                  label="ISO Image"
                  name="iso"
                  value={vmsToCreate[currentVMIndex].iso}
                  onChange={handleInputChange}
                  options={isoImages.map(iso => ({
                    value: iso.volid,
                    label: `${iso.volid} (${(iso.size / 1024 / 1024 / 1024).toFixed(2)} GB)`
                  }))}
                  helper="Select an ISO image to install the operating system. Upload ISOs to Proxmox storage first."
                  disabled={disabled}
                  loading={loadingResources}
                />
                <FormSelect
                  label="OS Type"
                  name="os_type"
                  value={vmsToCreate[currentVMIndex].os_type}
                  onChange={handleInputChange}
                  options={[
                    { value: 'linux', label: 'Linux' },
                    { value: 'windows', label: 'Windows' }
                  ]}
                  required
                  helper="Operating system type affects BIOS and driver settings."
                  disabled={disabled}
                />

                {/* VirtIO Drivers ISO - Only for Windows */}
                {vmsToCreate[currentVMIndex].os_type === 'windows' && (
                  <div>
                    <FormSelect
                      label="VirtIO Drivers ISO (Highly Recommended)"
                      name="virtio_iso"
                      value={vmsToCreate[currentVMIndex].virtio_iso}
                      onChange={handleInputChange}
                      options={[
                        { value: '', label: '-- No VirtIO ISO (Not Recommended) --' },
                        ...isoImages
                          .filter(iso => iso.volid.toLowerCase().includes('virtio'))
                          .map(iso => ({
                            value: iso.volid,
                            label: `${iso.volid} (${(iso.size / 1024 / 1024 / 1024).toFixed(2)} GB)`
                          })),
                        ...isoImages
                          .filter(iso => !iso.volid.toLowerCase().includes('virtio'))
                          .map(iso => ({
                            value: iso.volid,
                            label: `${iso.volid} (${(iso.size / 1024 / 1024 / 1024).toFixed(2)} GB)`
                          }))
                      ]}
                      helper="VirtIO drivers ISO will be attached as a second CD/DVD drive. Required for disk detection during Windows installation and optimal performance."
                      disabled={disabled}
                      loading={loadingResources}
                    />
                    {vmsToCreate[currentVMIndex].virtio_iso && (
                      <div className="mt-2 bg-blue-900/20 border border-blue-700 rounded-lg p-3">
                        <p className="text-xs text-blue-400">
                          ✓ Both ISOs will be attached: Windows ISO on ide2 (bootable), VirtIO drivers on ide0 (for driver installation)
                        </p>
                      </div>
                    )}
                    {!vmsToCreate[currentVMIndex].virtio_iso && (
                      <div className="mt-2 bg-yellow-900/20 border border-yellow-700 rounded-lg p-3">
                        <p className="text-xs text-yellow-400">
                          ⚠️ Without VirtIO drivers, Windows cannot detect the disk during installation. You'll need to attach the VirtIO ISO manually later.
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Windows Best Practices Banner */}
                {vmsToCreate[currentVMIndex].os_type === 'windows' && (
                  <div className="bg-green-900/20 border border-green-700 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-green-400 mb-2 flex items-center">
                      <CheckCircleIcon className="h-5 w-5 mr-2" />
                      Windows Best Practices Applied (Proxmox Recommended)
                    </h4>
                    <ul className="text-xs text-green-300 space-y-1 ml-7">
                      <li>✓ BIOS: OVMF (UEFI) with EFI disk - Required for Windows 11, recommended for Server 2022</li>
                      <li>✓ Machine: Q35 - Modern chipset with PCIe support</li>
                      <li>✓ CPU: host - Best performance with hardware passthrough</li>
                      <li>✓ Storage: VirtIO SCSI - High performance disk controller</li>
                      <li>✓ Network: VirtIO - Best network performance</li>
                      <li>✓ Boot Order: CD/DVD (Windows ISO) → Hard Disk</li>
                    </ul>
                    <div className="mt-3 ml-7 space-y-2">
                      <p className="text-xs text-green-400 font-medium">
                        📀 Dual ISO Configuration:
                      </p>
                      <ul className="text-xs text-green-300 space-y-1 ml-4">
                        <li>• Bootable CD/DVD (ide2): Windows installation ISO</li>
                        <li>• Drivers CD/DVD (ide0): VirtIO drivers ISO (non-bootable)</li>
                        <li>• EFI Disk: Automatically created for UEFI boot variables</li>
                        <li>• Boot order: ide2 (Windows ISO) → scsi0 (Hard Disk)</li>
                      </ul>
                      <p className="text-xs text-green-400 font-medium mt-2">
                        📥 During Windows Installation:
                      </p>
                      <ol className="text-xs text-green-300 space-y-1 ml-4 list-decimal">
                        <li>Boot from Windows ISO</li>
                        <li>At disk selection, click "Load Driver"</li>
                        <li>Browse the VirtIO CD (usually D: or E:)</li>
                        <li>Navigate to viostor\w10\amd64 (or w11\amd64 for Windows 11)</li>
                        <li>Select the driver and continue installation</li>
                        <li>After Windows installation, install remaining drivers from VirtIO ISO</li>
                      </ol>
                      {!vmsToCreate[currentVMIndex].virtio_iso && (
                        <p className="text-xs text-yellow-400 mt-2">
                          ⚠️ Don't forget to select VirtIO Drivers ISO above!
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* System Section */}
          <div className="border border-dark-border rounded-lg overflow-hidden">
            <SectionHeader title="System" section="system" icon={PlusCircleIcon} />
            {expandedSections.system && (
              <div className="p-4 space-y-4">
                {/* Windows auto-config notice */}
                {vmsToCreate[currentVMIndex].os_type === 'windows' && (
                  <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-3">
                    <p className="text-sm text-blue-400">
                      ℹ️ System settings have been automatically configured for Windows best practices
                    </p>
                  </div>
                )}

                <FormSelect
                  label="BIOS"
                  name="bios"
                  value={vmsToCreate[currentVMIndex].bios}
                  onChange={handleInputChange}
                  options={[
                    { value: 'seabios', label: 'SeaBIOS (Legacy BIOS)' },
                    { value: 'ovmf', label: 'OVMF (UEFI) - Required for Windows 11' }
                  ]}
                  helper={
                    vmsToCreate[currentVMIndex].os_type === 'windows'
                      ? "OVMF (UEFI) is required for Windows 11 and recommended for Windows Server 2022."
                      : "BIOS type. Use OVMF for UEFI, SeaBIOS for legacy BIOS."
                  }
                  disabled={disabled}
                />

                <FormSelect
                  label="Machine Type"
                  name="machine"
                  value={vmsToCreate[currentVMIndex].machine}
                  onChange={handleInputChange}
                  options={[
                    { value: 'q35', label: 'Q35 (Modern - Recommended)' },
                    { value: 'i440fx', label: 'i440fx (Legacy)' }
                  ]}
                  helper="Machine type. Q35 provides modern chipset with PCIe support."
                  disabled={disabled}
                />

                <FormSelect
                  label="CPU Type"
                  name="cpu_type"
                  value={vmsToCreate[currentVMIndex].cpu_type}
                  onChange={handleInputChange}
                  options={[
                    { value: 'host', label: 'host (Best Performance - Recommended)' },
                    { value: 'kvm64', label: 'kvm64 (Generic 64-bit)' },
                    { value: 'qemu64', label: 'qemu64 (Maximum Compatibility)' }
                  ]}
                  helper="CPU type. 'host' provides best performance by exposing all host CPU features to the VM."
                  disabled={disabled}
                />
              </div>
            )}
          </div>

          {/* Disks Section */}
          <div className="border border-dark-border rounded-lg overflow-hidden">
            <SectionHeader title="Disks" section="disks" icon={PlusCircleIcon} />
            {expandedSections.disks && (
              <div className="p-4 space-y-4">
                <FormSelect
                  label="Storage"
                  name="storage"
                  value={vmsToCreate[currentVMIndex].storage}
                  onChange={handleInputChange}
                  options={storages.filter(s => s.active).map(storage => ({
                    value: storage.storage,
                    label: `${storage.storage} (${storage.type}) - ${storage.avail ? (storage.avail / 1024 / 1024 / 1024).toFixed(2) + ' GB free' : 'N/A'}`
                  }))}
                  required
                  helper="Storage pool for the VM disk. Choose one with enough free space."
                  disabled={disabled}
                  loading={loadingResources}
                />
                <FormInput
                  label="Disk Size (GB)"
                  name="disk_size"
                  type="number"
                  value={vmsToCreate[currentVMIndex].disk_size}
                  onChange={handleInputChange}
                  min={10}
                  max={2000}
                  required
                  helper="Virtual disk size in gigabytes. Plan for OS (10-20GB) + applications + data."
                  disabled={disabled}
                />
              </div>
            )}
          </div>

          {/* CPU Section */}
          <div className="border border-dark-border rounded-lg overflow-hidden">
            <SectionHeader title="CPU" section="cpu" icon={PlusCircleIcon} />
            {expandedSections.cpu && (
              <div className="p-4 space-y-4">
                <FormInput
                  label="Sockets"
                  name="sockets"
                  type="number"
                  value={vmsToCreate[currentVMIndex].sockets}
                  onChange={handleInputChange}
                  min={1}
                  max={4}
                  required
                  helper="Number of CPU sockets. Usually 1 is sufficient."
                  disabled={disabled}
                />
                <FormInput
                  label="Cores per Socket"
                  name="cores"
                  type="number"
                  value={vmsToCreate[currentVMIndex].cores}
                  onChange={handleInputChange}
                  min={1}
                  max={32}
                  required
                  helper="CPU cores per socket. Total vCPUs = Sockets × Cores. Common: 2-4 for web servers, 8+ for databases."
                  disabled={disabled}
                />
                <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-3">
                  <p className="text-sm text-blue-400">
                    Total vCPUs: <span className="font-bold">{vmsToCreate[currentVMIndex].sockets * vmsToCreate[currentVMIndex].cores}</span>
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Memory Section */}
          <div className="border border-dark-border rounded-lg overflow-hidden">
            <SectionHeader title="Memory" section="memory" icon={PlusCircleIcon} />
            {expandedSections.memory && (
              <div className="p-4 space-y-4">
                <FormInput
                  label="Memory (MB)"
                  name="memory"
                  type="number"
                  value={vmsToCreate[currentVMIndex].memory}
                  onChange={handleInputChange}
                  min={512}
                  max={65536}
                  required
                  helper="RAM in megabytes. Common values: 2048 (2GB), 4096 (4GB), 8192 (8GB), 16384 (16GB)."
                  disabled={disabled}
                />
                <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-3">
                  <p className="text-sm text-blue-400">
                    Memory: <span className="font-bold">{(vmsToCreate[currentVMIndex].memory / 1024).toFixed(2)} GB</span>
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Network Section */}
          <div className="border border-dark-border rounded-lg overflow-hidden">
            <SectionHeader title="Network" section="network" icon={PlusCircleIcon} />
            {expandedSections.network && (
              <div className="p-4 space-y-4">
                <FormSelect
                  label="Bridge"
                  name="network_bridge"
                  value={vmsToCreate[currentVMIndex].network_bridge}
                  onChange={handleInputChange}
                  options={networkBridges.filter(n => n.active).map(bridge => ({
                    value: bridge.iface,
                    label: `${bridge.iface} (${bridge.type})`
                  }))}
                  required
                  helper="Network bridge to connect the VM. Usually vmbr0."
                  disabled={disabled}
                  loading={loadingResources}
                />
                <FormSelect
                  label="Model"
                  name="network_model"
                  value={vmsToCreate[currentVMIndex].network_model}
                  onChange={handleInputChange}
                  options={[
                    { value: 'virtio', label: 'VirtIO (Recommended)' },
                    { value: 'e1000', label: 'Intel E1000' },
                    { value: 'rtl8139', label: 'Realtek RTL8139' }
                  ]}
                  helper="Network card model. VirtIO provides best performance with proper drivers."
                  disabled={disabled}
                />
              </div>
            )}
          </div>

          {/* Tags Section */}
          <div className="border border-dark-border rounded-lg overflow-hidden">
            <SectionHeader title="Tags" section="tags" icon={PlusCircleIcon} />
            {expandedSections.tags && (
              <div className="p-4">
                <TagInput
                  tags={vmsToCreate[currentVMIndex].tags}
                  onChange={handleTagsChange}
                  disabled={disabled}
                  helper="Add tags to organize and categorize your VMs. Tags help with filtering and management in Proxmox. Use alphanumeric characters, hyphens, and underscores."
                />
              </div>
            )}
          </div>

          {/* Options */}
          <div className="pt-4 border-t border-dark-border space-y-4">
            <FormCheckbox
              label="Enable QEMU Guest Agent (Recommended for Windows)"
              name="enable_guest_agent"
              checked={vmsToCreate[currentVMIndex].enable_guest_agent}
              onChange={handleInputChange}
              description={
                vmsToCreate[currentVMIndex].os_type === 'windows'
                  ? "Enables better VM integration with Proxmox: IP address detection, graceful shutdown, snapshot consistency. Install the guest agent from VirtIO drivers ISO after Windows installation."
                  : "Enables QEMU Guest Agent for better VM integration (IP detection, graceful shutdown). Install qemu-guest-agent package inside the VM after OS installation."
              }
              disabled={disabled}
            />

            <FormCheckbox
              label="Start VM After Creation"
              name="start_on_creation"
              checked={vmsToCreate[currentVMIndex].start_on_creation}
              onChange={handleInputChange}
              description="Automatically start the VM and boot from the ISO after creation."
              disabled={disabled}
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={disabled || submitting || loadingResources}
            className="
              w-full flex items-center justify-center px-6 py-3
              bg-blue-600 hover:bg-blue-700
              text-white font-medium rounded-lg
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-dark-bg
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-colors
            "
          >
            {submitting ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Creating {vmsToCreate.length} VM{vmsToCreate.length > 1 ? 's' : ''}...
              </>
            ) : (
              <>
                <PlusCircleIcon className="h-5 w-5 mr-2" />
                Create {vmsToCreate.length} VM{vmsToCreate.length > 1 ? 's' : ''}
              </>
            )}
          </button>
        </form>
      )}

      {/* Deployment Result */}
      {result && (
        <div className="border-t border-dark-border">
          <DeploymentStatus result={result} />
        </div>
      )}
    </div>
  )
}
