import { useState, useEffect } from 'react'
import { ServerIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/solid'
import { checkProxmoxStatus } from './services/api'
import TemplateCloneForm from './components/TemplateCloneForm'
import VMCreateForm from './components/VMCreateForm'
import Header from './components/Header'
import TabButton from './components/TabButton'

function App() {
  const [activeTab, setActiveTab] = useState('clone')
  const [proxmoxStatus, setProxmoxStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkConnection()
  }, [])

  const checkConnection = async () => {
    try {
      const response = await checkProxmoxStatus()
      setProxmoxStatus(response.data)
    } catch (error) {
      console.error('Failed to connect to Proxmox:', error)
      setProxmoxStatus({ connected: false, message: 'Failed to connect to API' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-bg">
      <Header />

      {/* Connection Status Banner */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        {loading ? (
          <div className="bg-dark-surface border border-dark-border rounded-lg p-4 flex items-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500 mr-3"></div>
            <span className="text-dark-muted">Checking Proxmox connection...</span>
          </div>
        ) : proxmoxStatus?.connected ? (
          <div className="bg-green-900/20 border border-green-700 rounded-lg p-4 flex items-center">
            <CheckCircleIcon className="h-5 w-5 text-green-500 mr-3" />
            <div>
              <span className="text-green-400 font-medium">Connected to Proxmox</span>
              <span className="text-dark-muted ml-2">
                ({proxmoxStatus.proxmox_host} - {proxmoxStatus.nodes_count} nodes)
              </span>
            </div>
          </div>
        ) : (
          <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 flex items-center">
            <XCircleIcon className="h-5 w-5 text-red-500 mr-3" />
            <div>
              <span className="text-red-400 font-medium">Proxmox Connection Failed</span>
              <span className="text-dark-muted ml-2">{proxmoxStatus?.message}</span>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="border-b border-dark-border mb-8">
          <nav className="-mb-px flex space-x-8">
            <TabButton
              active={activeTab === 'clone'}
              onClick={() => setActiveTab('clone')}
              icon={ServerIcon}
              label="Clone from Template"
              description="Recommended"
            />
            <TabButton
              active={activeTab === 'create'}
              onClick={() => setActiveTab('create')}
              icon={ServerIcon}
              label="Create New VM"
              description="Advanced"
            />
          </nav>
        </div>

        {/* Tab Content */}
        <div className="mt-8">
          {activeTab === 'clone' ? (
            <TemplateCloneForm disabled={!proxmoxStatus?.connected} />
          ) : (
            <VMCreateForm disabled={!proxmoxStatus?.connected} />
          )}
        </div>
      </div>
    </div>
  )
}

export default App
