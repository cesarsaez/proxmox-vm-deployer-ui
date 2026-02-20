import { useState, useEffect } from 'react'
import { DocumentDuplicateIcon, CheckCircleIcon, PlusCircleIcon, TrashIcon } from '@heroicons/react/24/solid'
import { listTemplates, batchCloneTemplate } from '../services/api'
import FormInput from './FormInput'
import FormSelect from './FormSelect'
import FormCheckbox from './FormCheckbox'
import TagInput from './TagInput'
import DeploymentStatus from './DeploymentStatus'

export default function TemplateCloneForm({ disabled }) {
  const [templates, setTemplates] = useState([])
  const [loadingTemplates, setLoadingTemplates] = useState(true)
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  // Array of VMs to clone
  const [vmsToClone, setVmsToClone] = useState([{
    source_vmid: '',
    new_vmid: '',
    name: '',
    cores: 2,
    memory: 2048,
    full_clone: true,
    start_after_clone: false,
    tags: [],
    // Cloud-init configuration (for Ubuntu VMs)
    enable_cloudinit: false,
    cloudinit: {
      ipconfig: '',
      nameserver: '8.8.8.8',
      searchdomain: 'local',
      username: '',
      ssh_keys: '',
      sudo: true,
      groups: 'sudo',
      packages: '',
      runcmd: ''
    }
  }])

  const [currentVMIndex, setCurrentVMIndex] = useState(0)

  useEffect(() => {
    loadTemplates()
  }, [])

  const loadTemplates = async () => {
    try {
      const response = await listTemplates()
      setTemplates(response.data.templates || [])
      if (response.data.templates.length === 0) {
        setError('No templates found. Please create templates in Proxmox first.')
      }
    } catch (err) {
      console.error('Failed to load templates:', err)
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to connect to API. Please check that the backend is running.'
      setError(errorMsg)
    } finally {
      setLoadingTemplates(false)
    }
  }

  const handleTemplateChange = (e) => {
    const vmid = e.target.value
    const updatedVMs = [...vmsToClone]
    updatedVMs[currentVMIndex] = { ...updatedVMs[currentVMIndex], source_vmid: vmid }
    setVmsToClone(updatedVMs)

    const template = templates.find(t => t.vmid === parseInt(vmid))
    setSelectedTemplate(template)
  }

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target
    const updatedVMs = [...vmsToClone]
    updatedVMs[currentVMIndex] = {
      ...updatedVMs[currentVMIndex],
      [name]: type === 'checkbox' ? checked : value
    }
    setVmsToClone(updatedVMs)
  }

  const handleTagsChange = (newTags) => {
    const updatedVMs = [...vmsToClone]
    updatedVMs[currentVMIndex] = { ...updatedVMs[currentVMIndex], tags: newTags }
    setVmsToClone(updatedVMs)
  }

  const handleCloudInitChange = (e) => {
    const { name, value, type, checked } = e.target
    const updatedVMs = [...vmsToClone]
    const fieldName = name.replace('cloudinit.', '')

    if (name === 'enable_cloudinit') {
      updatedVMs[currentVMIndex] = {
        ...updatedVMs[currentVMIndex],
        enable_cloudinit: checked
      }
    } else {
      updatedVMs[currentVMIndex] = {
        ...updatedVMs[currentVMIndex],
        cloudinit: {
          ...updatedVMs[currentVMIndex].cloudinit,
          [fieldName]: type === 'checkbox' ? checked : value
        }
      }
    }
    setVmsToClone(updatedVMs)
  }

  const addVM = () => {
    // Copy current VM data but clear name and new_vmid
    const lastVM = vmsToClone[vmsToClone.length - 1]
    const newVM = {
      ...lastVM,
      name: '',
      new_vmid: ''
    }
    setVmsToClone([...vmsToClone, newVM])
    setCurrentVMIndex(vmsToClone.length)
  }

  const removeVM = (index) => {
    if (vmsToClone.length === 1) return // Don't remove if only one
    const updatedVMs = vmsToClone.filter((_, i) => i !== index)
    setVmsToClone(updatedVMs)
    // Adjust current index if needed
    if (currentVMIndex >= updatedVMs.length) {
      setCurrentVMIndex(updatedVMs.length - 1)
    }
  }

  const selectVM = (index) => {
    setCurrentVMIndex(index)
    // Update selected template based on the VM being selected
    const vm = vmsToClone[index]
    if (vm.source_vmid) {
      const template = templates.find(t => t.vmid === parseInt(vm.source_vmid))
      setSelectedTemplate(template)
    } else {
      setSelectedTemplate(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    setResult(null)

    try {
      // Prepare all VMs for submission
      const payload = vmsToClone.map(vm => {
        const vmPayload = {
          source_vmid: parseInt(vm.source_vmid),
          new_vmid: vm.new_vmid ? parseInt(vm.new_vmid) : undefined,
          name: vm.name,
          cores: parseInt(vm.cores),
          memory: parseInt(vm.memory),
          full_clone: vm.full_clone,
          start_after_clone: vm.start_after_clone,
          tags: vm.tags.length > 0 ? vm.tags : undefined
        }

        // Add cloud-init configuration if enabled
        if (vm.enable_cloudinit && vm.cloudinit.username) {
          const cloudinit = {
            ipconfig: vm.cloudinit.ipconfig || undefined,
            nameserver: vm.cloudinit.nameserver || undefined,
            searchdomain: vm.cloudinit.searchdomain || undefined,
            users: [{
              username: vm.cloudinit.username,
              ssh_keys: vm.cloudinit.ssh_keys ? vm.cloudinit.ssh_keys.split('\n').filter(k => k.trim()) : undefined,
              sudo: vm.cloudinit.sudo,
              groups: vm.cloudinit.groups ? vm.cloudinit.groups.split(',').map(g => g.trim()).filter(g => g) : undefined
            }],
            packages: vm.cloudinit.packages ? vm.cloudinit.packages.split(',').map(p => p.trim()).filter(p => p) : undefined,
            runcmd: vm.cloudinit.runcmd ? vm.cloudinit.runcmd.split('\n').filter(c => c.trim()) : undefined
          }

          // Only include cloud-init if username is provided
          if (cloudinit.users[0].username) {
            vmPayload.cloudinit = cloudinit
          }
        }

        return vmPayload
      })

      const response = await batchCloneTemplate(payload)
      setResult(response.data)

      // Reset form on success
      setVmsToClone([{
        source_vmid: '',
        new_vmid: '',
        name: '',
        cores: 2,
        memory: 2048,
        full_clone: true,
        start_after_clone: false,
        tags: [],
        enable_cloudinit: false,
        cloudinit: {
          ipconfig: '',
          nameserver: '8.8.8.8',
          searchdomain: 'local',
          username: '',
          ssh_keys: '',
          sudo: true,
          groups: 'sudo',
          packages: '',
          runcmd: ''
        }
      }])
      setCurrentVMIndex(0)
      setSelectedTemplate(null)
    } catch (err) {
      console.error('Clone failed:', err)
      setError(err.response?.data?.detail || 'Failed to clone template(s)')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="bg-dark-surface rounded-lg shadow-lg border border-dark-border">
      <div className="px-6 py-4 border-b border-dark-border">
        <h2 className="text-xl font-semibold text-dark-text flex items-center">
          <DocumentDuplicateIcon className="h-6 w-6 text-blue-500 mr-2" />
          Clone from Template
        </h2>
        <p className="text-dark-muted text-sm mt-1">
          Create a new VM by cloning an existing template
        </p>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-6">
        {/* VM List */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="block text-sm font-medium text-dark-text">
              VMs to Clone ({vmsToClone.length})
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

          <div className="flex gap-2 flex-wrap">
            {vmsToClone.map((vm, index) => (
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

                {vmsToClone.length > 1 && (
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
        </div>

        <div className="border-t border-dark-border pt-6">
          <h3 className="text-lg font-medium text-dark-text mb-4">
            Configure VM {currentVMIndex + 1}
          </h3>

          {/* Template Selection */}
          <div className="space-y-6">
            <FormSelect
              label="Template"
              name="source_vmid"
              value={vmsToClone[currentVMIndex].source_vmid}
              onChange={handleTemplateChange}
              options={templates.map(t => ({
                value: t.vmid,
                label: `${t.name} (ID: ${t.vmid}) - ${t.cores} cores, ${t.memory}MB RAM`
              }))}
              required
              helper="Select the template you want to clone from. Templates are pre-configured VMs ready for deployment."
              disabled={disabled}
              loading={loadingTemplates}
            />

            {/* Template Info */}
            {selectedTemplate && (
              <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
                <h3 className="text-sm font-medium text-blue-400 mb-2">Template Information</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="text-dark-muted">Node:</div>
                  <div className="text-dark-text">{selectedTemplate.node}</div>
                  <div className="text-dark-muted">Status:</div>
                  <div className="text-dark-text">{selectedTemplate.status}</div>
                  <div className="text-dark-muted">Cores:</div>
                  <div className="text-dark-text">{selectedTemplate.cores}</div>
                  <div className="text-dark-muted">Memory:</div>
                  <div className="text-dark-text">{selectedTemplate.memory} MB</div>
                </div>
              </div>
            )}

            {/* New VM ID */}
            <FormInput
              label="New VM ID"
              name="new_vmid"
              type="number"
              value={vmsToClone[currentVMIndex].new_vmid}
              onChange={handleInputChange}
              placeholder="Leave empty for auto-assignment"
              helper="Unique VM ID (100-999999). Leave empty to automatically assign the next available ID."
              disabled={disabled}
              min={100}
              max={999999}
            />

            {/* VM Name */}
            <FormInput
              label="VM Name"
              name="name"
              value={vmsToClone[currentVMIndex].name}
              onChange={handleInputChange}
              placeholder="e.g., web-server-01"
              required
              helper="A unique name for your new VM. Use lowercase letters, numbers, and hyphens."
              disabled={disabled}
            />

            {/* CPU Cores */}
            <FormInput
              label="CPU Cores"
              name="cores"
              type="number"
              value={vmsToClone[currentVMIndex].cores}
              onChange={handleInputChange}
              min={1}
              max={32}
              required
              helper="Number of CPU cores to allocate to the VM. More cores = better performance for multi-threaded applications."
              disabled={disabled}
            />

            {/* Memory */}
            <FormInput
              label="Memory (MB)"
              name="memory"
              type="number"
              value={vmsToClone[currentVMIndex].memory}
              onChange={handleInputChange}
              min={512}
              max={32768}
              required
              helper="Amount of RAM in megabytes. Typical values: 2048 (2GB), 4096 (4GB), 8192 (8GB)."
              disabled={disabled}
            />

            {/* Tags */}
            <TagInput
              tags={vmsToClone[currentVMIndex].tags}
              onChange={handleTagsChange}
              disabled={disabled}
              helper="Add tags to organize and categorize your VMs. Tags help with filtering and management in Proxmox."
            />

            {/* Clone Options */}
            <div className="space-y-4 pt-4 border-t border-dark-border">
              <FormCheckbox
                label="Full Clone"
                name="full_clone"
                checked={vmsToClone[currentVMIndex].full_clone}
                onChange={handleInputChange}
                description="Create an independent copy (recommended). Linked clones are faster but depend on the template."
                disabled={disabled}
              />

              <FormCheckbox
                label="Start After Clone"
                name="start_after_clone"
                checked={vmsToClone[currentVMIndex].start_after_clone}
                onChange={handleInputChange}
                description="Automatically start the VM after cloning is complete."
                disabled={disabled}
              />
            </div>

            {/* Cloud-Init Configuration (Ubuntu VMs) */}
            <div className="space-y-4 pt-6 border-t border-dark-border">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-base font-medium text-dark-text flex items-center gap-2">
                    <svg className="h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                    </svg>
                    Cloud-Init Configuration
                  </h4>
                  <p className="text-xs text-dark-muted mt-1">
                    For Ubuntu cloud images - automatically configure users, network, and packages
                  </p>
                </div>
                <FormCheckbox
                  label=""
                  name="enable_cloudinit"
                  checked={vmsToClone[currentVMIndex].enable_cloudinit}
                  onChange={handleCloudInitChange}
                  description=""
                  disabled={disabled}
                />
              </div>

              {vmsToClone[currentVMIndex].enable_cloudinit && (
                <div className="space-y-4 bg-dark-bg p-4 rounded-lg border border-dark-border">
                  {/* Network Configuration */}
                  <div className="space-y-3">
                    <h5 className="text-sm font-medium text-dark-text">Network Configuration</h5>

                    <FormInput
                      label="IP Configuration"
                      name="cloudinit.ipconfig"
                      value={vmsToClone[currentVMIndex].cloudinit.ipconfig}
                      onChange={handleCloudInitChange}
                      placeholder="ip=192.168.1.100/24,gw=192.168.1.1"
                      helper="Static IP configuration. Format: ip=<ip>/<netmask>,gw=<gateway>. Leave empty for DHCP."
                      disabled={disabled}
                    />

                    <div className="grid grid-cols-2 gap-4">
                      <FormInput
                        label="DNS Nameserver"
                        name="cloudinit.nameserver"
                        value={vmsToClone[currentVMIndex].cloudinit.nameserver}
                        onChange={handleCloudInitChange}
                        placeholder="8.8.8.8"
                        helper="DNS server IP address"
                        disabled={disabled}
                      />

                      <FormInput
                        label="Search Domain"
                        name="cloudinit.searchdomain"
                        value={vmsToClone[currentVMIndex].cloudinit.searchdomain}
                        onChange={handleCloudInitChange}
                        placeholder="local"
                        helper="DNS search domain"
                        disabled={disabled}
                      />
                    </div>
                  </div>

                  {/* User Configuration */}
                  <div className="space-y-3 pt-4 border-t border-dark-border">
                    <h5 className="text-sm font-medium text-dark-text">User Configuration</h5>

                    <FormInput
                      label="Username"
                      name="cloudinit.username"
                      value={vmsToClone[currentVMIndex].cloudinit.username}
                      onChange={handleCloudInitChange}
                      placeholder="ubuntu"
                      required={vmsToClone[currentVMIndex].enable_cloudinit}
                      helper="Username for the new user account"
                      disabled={disabled}
                    />

                    <div>
                      <label className="block text-sm font-medium text-dark-text mb-1">
                        SSH Public Keys
                      </label>
                      <textarea
                        name="cloudinit.ssh_keys"
                        value={vmsToClone[currentVMIndex].cloudinit.ssh_keys}
                        onChange={handleCloudInitChange}
                        placeholder="ssh-rsa AAAAB3NzaC1yc2E... user@host"
                        rows={3}
                        disabled={disabled}
                        className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-dark-text placeholder-dark-muted focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed font-mono text-xs"
                      />
                      <p className="text-xs text-dark-muted mt-1">
                        SSH public keys for passwordless login (one per line)
                      </p>
                    </div>

                    <div className="flex items-center gap-4">
                      <FormCheckbox
                        label="Grant Sudo Access"
                        name="cloudinit.sudo"
                        checked={vmsToClone[currentVMIndex].cloudinit.sudo}
                        onChange={handleCloudInitChange}
                        description="Allow user to run commands with sudo (passwordless)"
                        disabled={disabled}
                      />
                    </div>

                    <FormInput
                      label="Groups"
                      name="cloudinit.groups"
                      value={vmsToClone[currentVMIndex].cloudinit.groups}
                      onChange={handleCloudInitChange}
                      placeholder="sudo,docker,users"
                      helper="Comma-separated list of groups for the user"
                      disabled={disabled}
                    />
                  </div>

                  {/* Packages and Commands */}
                  <div className="space-y-3 pt-4 border-t border-dark-border">
                    <h5 className="text-sm font-medium text-dark-text">Software & Commands</h5>

                    <FormInput
                      label="Packages to Install"
                      name="cloudinit.packages"
                      value={vmsToClone[currentVMIndex].cloudinit.packages}
                      onChange={handleCloudInitChange}
                      placeholder="vim,curl,git,docker.io,htop"
                      helper="Comma-separated list of packages to install on first boot"
                      disabled={disabled}
                    />

                    <div>
                      <label className="block text-sm font-medium text-dark-text mb-1">
                        Custom Commands
                      </label>
                      <textarea
                        name="cloudinit.runcmd"
                        value={vmsToClone[currentVMIndex].cloudinit.runcmd}
                        onChange={handleCloudInitChange}
                        placeholder="systemctl enable docker&#10;systemctl start docker&#10;echo 'Setup complete' > /root/setup.log"
                        rows={3}
                        disabled={disabled}
                        className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-dark-text placeholder-dark-muted focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed font-mono text-xs"
                      />
                      <p className="text-xs text-dark-muted mt-1">
                        Shell commands to run after setup (one per line)
                      </p>
                    </div>
                  </div>

                  {/* Info Box */}
                  <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-3 mt-4">
                    <p className="text-xs text-blue-300">
                      <strong>Note:</strong> Cloud-init runs on first boot and may take 2-3 minutes to complete.
                      The VM will be accessible once cloud-init finishes configuring the system.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
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
          disabled={disabled || submitting || !vmsToClone[currentVMIndex].source_vmid}
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
              Cloning {vmsToClone.length} VM{vmsToClone.length > 1 ? 's' : ''}...
            </>
          ) : (
            <>
              <DocumentDuplicateIcon className="h-5 w-5 mr-2" />
              Clone {vmsToClone.length} VM{vmsToClone.length > 1 ? 's' : ''}
            </>
          )}
        </button>
      </form>

      {/* Deployment Result */}
      {result && (
        <div className="border-t border-dark-border">
          <DeploymentStatus result={result} />
        </div>
      )}
    </div>
  )
}
