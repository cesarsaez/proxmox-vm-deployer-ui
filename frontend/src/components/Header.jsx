import { ServerIcon } from '@heroicons/react/24/solid'

export default function Header() {
  return (
    <header className="bg-dark-surface border-b border-dark-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center">
          <ServerIcon className="h-10 w-10 text-blue-500 mr-4" />
          <div>
            <h1 className="text-3xl font-bold text-dark-text">
              Proxmox VM Deployer
            </h1>
            <p className="text-dark-muted mt-1">
              Deploy and manage virtual machines with ease
            </p>
          </div>
        </div>
      </div>
    </header>
  )
}
