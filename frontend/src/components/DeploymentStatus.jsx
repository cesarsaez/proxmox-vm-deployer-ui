import { useState } from 'react'
import { CheckCircleIcon, PlayIcon } from '@heroicons/react/24/solid'
import { validateVM } from '../services/api'

export default function DeploymentStatus({ result }) {
  const [validating, setValidating] = useState(false)
  const [validation, setValidation] = useState(null)
  const [validationError, setValidationError] = useState(null)

  const handleValidate = async () => {
    setValidating(true)
    setValidationError(null)

    try {
      const response = await validateVM(result.vmid, 'linux')
      setValidation(response.data)
    } catch (err) {
      console.error('Validation failed:', err)
      setValidationError('Failed to validate VM. The VM may still be booting.')
    } finally {
      setValidating(false)
    }
  }

  return (
    <div className="p-6 space-y-4">
      {/* Success Message */}
      <div className="bg-green-900/20 border border-green-700 rounded-lg p-4">
        <div className="flex items-start">
          <CheckCircleIcon className="h-6 w-6 text-green-500 mr-3 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-green-400 mb-2">
              {result.status === 'started' ? 'VM Created and Started!' : 'VM Created Successfully!'}
            </h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-dark-muted">VM ID:</span>
                <span className="text-dark-text font-mono">{result.vmid}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-dark-muted">Name:</span>
                <span className="text-dark-text">{result.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-dark-muted">Node:</span>
                <span className="text-dark-text">{result.node}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-dark-muted">Status:</span>
                <span className="text-green-400">{result.status}</span>
              </div>
            </div>
            <p className="text-dark-muted text-sm mt-3">{result.message}</p>
          </div>
        </div>
      </div>

      {/* Validate Button */}
      {result.status === 'started' && !validation && (
        <button
          onClick={handleValidate}
          disabled={validating}
          className="
            w-full flex items-center justify-center px-6 py-3
            bg-blue-600 hover:bg-blue-700
            text-white font-medium rounded-lg
            focus:outline-none focus:ring-2 focus:ring-blue-500
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors
          "
        >
          {validating ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              Validating VM...
            </>
          ) : (
            <>
              <PlayIcon className="h-5 w-5 mr-2" />
              Run Post-Deployment Validation
            </>
          )}
        </button>
      )}

      {/* Validation Error */}
      {validationError && (
        <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
          <p className="text-yellow-400 text-sm">{validationError}</p>
        </div>
      )}

      {/* Validation Results */}
      {validation && (
        <div className={`
          border rounded-lg p-4
          ${validation.status === 'healthy'
            ? 'bg-green-900/20 border-green-700'
            : 'bg-yellow-900/20 border-yellow-700'}
        `}>
          <h3 className="font-semibold mb-3 flex items-center">
            <CheckCircleIcon className={`h-5 w-5 mr-2 ${
              validation.status === 'healthy' ? 'text-green-500' : 'text-yellow-500'
            }`} />
            <span className={validation.status === 'healthy' ? 'text-green-400' : 'text-yellow-400'}>
              Validation: {validation.status.toUpperCase()}
            </span>
          </h3>

          {validation.ip_address && (
            <div className="mb-3 pb-3 border-b border-dark-border">
              <span className="text-dark-muted text-sm">IP Address: </span>
              <span className="text-dark-text font-mono">{validation.ip_address}</span>
            </div>
          )}

          <div className="space-y-2">
            {Object.entries(validation.checks).map(([key, check]) => (
              <div key={key} className="flex items-center text-sm">
                <CheckCircleIcon className={`h-4 w-4 mr-2 ${
                  check.passed ? 'text-green-500' : 'text-red-500'
                }`} />
                <span className="text-dark-muted capitalize">
                  {key.replace(/_/g, ' ')}:
                </span>
                <span className={`ml-2 ${check.passed ? 'text-green-400' : 'text-red-400'}`}>
                  {check.passed ? 'Passed' : 'Failed'}
                </span>
                {check.message && (
                  <span className="ml-2 text-dark-muted text-xs">
                    ({check.message})
                  </span>
                )}
              </div>
            ))}
          </div>

          {validation.message && (
            <p className="text-dark-muted text-sm mt-3 pt-3 border-t border-dark-border">
              {validation.message}
            </p>
          )}
        </div>
      )}

      {/* Next Steps */}
      {result.status === 'created' && (
        <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
          <h3 className="text-sm font-medium text-blue-400 mb-2">Next Steps</h3>
          <ul className="text-sm text-dark-muted space-y-1 list-disc list-inside">
            <li>Start the VM from the Proxmox web interface</li>
            <li>Access the console to complete OS setup if needed</li>
            <li>Configure network settings and install QEMU guest agent</li>
          </ul>
        </div>
      )}
    </div>
  )
}
