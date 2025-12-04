import { useState } from 'react'

/**
 * DateRangeSelector Component
 *
 * Provides preset date range options and custom date range selection
 * for filtering dashboard analytics.
 *
 * @param {Object} props
 * @param {Function} props.onChange - Callback when date range changes (receives {from, to})
 * @param {string} props.defaultValue - Default preset value ('30d', '7d', etc.)
 */
export default function DateRangeSelector({ onChange, defaultValue = '30d' }) {
  const [selectedPreset, setSelectedPreset] = useState(defaultValue)
  const [customFrom, setCustomFrom] = useState('')
  const [customTo, setCustomTo] = useState('')
  const [showCustom, setShowCustom] = useState(false)

  const calculateDateRange = (preset) => {
    const now = new Date()
    const to = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59)
    let from

    switch (preset) {
      case '7d':
        from = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
        break
      case '30d':
        from = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
        break
      case '3m':
        from = new Date(now.getFullYear(), now.getMonth() - 3, 1)
        break
      case '6m':
        from = new Date(now.getFullYear(), now.getMonth() - 6, 1)
        break
      case '1y':
        from = new Date(now.getFullYear() - 1, now.getMonth(), 1)
        break
      case 'custom':
        return null // Custom handled separately
      default:
        from = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
    }

    from.setHours(0, 0, 0, 0)
    return {
      from: from.toISOString().split('T')[0],
      to: to.toISOString().split('T')[0],
    }
  }

  const handlePresetChange = (preset) => {
    setSelectedPreset(preset)
    setShowCustom(preset === 'custom')

    if (preset !== 'custom') {
      const range = calculateDateRange(preset)
      if (range) {
        onChange(range)
      }
    }
  }

  const handleCustomSubmit = () => {
    if (customFrom && customTo) {
      if (new Date(customFrom) > new Date(customTo)) {
        alert('Start date must be before end date')
        return
      }
      onChange({
        from: customFrom,
        to: customTo,
      })
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <label className="text-sm font-semibold text-neutral-700">Date Range:</label>
      <div className="flex flex-wrap gap-2">
        {['7d', '30d', '3m', '6m', '1y', 'custom'].map((preset) => (
          <button
            key={preset}
            type="button"
            onClick={() => handlePresetChange(preset)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              selectedPreset === preset
                ? 'bg-primary-600 text-white'
                : 'bg-white text-neutral-700 hover:bg-neutral-50 border border-neutral-200'
            }`}
          >
            {preset === '7d' && 'Last 7 Days'}
            {preset === '30d' && 'Last 30 Days'}
            {preset === '3m' && 'Last 3 Months'}
            {preset === '6m' && 'Last 6 Months'}
            {preset === '1y' && 'Last Year'}
            {preset === 'custom' && 'Custom'}
          </button>
        ))}
      </div>

      {showCustom && (
        <div className="flex items-center gap-2 border border-neutral-200 rounded-lg px-3 py-2 bg-white">
          <input
            type="date"
            value={customFrom}
            onChange={(e) => setCustomFrom(e.target.value)}
            className="text-sm border border-neutral-200 rounded px-2 py-1"
            placeholder="From"
          />
          <span className="text-neutral-500">to</span>
          <input
            type="date"
            value={customTo}
            onChange={(e) => setCustomTo(e.target.value)}
            className="text-sm border border-neutral-200 rounded px-2 py-1"
            placeholder="To"
          />
          <button
            type="button"
            onClick={handleCustomSubmit}
            className="px-3 py-1 text-sm font-medium text-white bg-primary-600 rounded hover:bg-primary-700"
          >
            Apply
          </button>
        </div>
      )}
    </div>
  )
}

