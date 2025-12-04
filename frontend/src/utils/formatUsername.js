/**
 * Format username for display.
 *
 * Converts acronyms (like "dsa") to uppercase, and properly capitalizes
 * other usernames (like "maintenance_officer" -> "Maintenance Officer").
 *
 * @param {string} username - The username to format
 * @returns {string} Formatted username for display
 */
export function formatUsername(username) {
  if (!username) return 'Guest'

  // Known acronyms that should be displayed in all uppercase
  const acronyms = ['dsa']

  const lowerUsername = username.toLowerCase()

  // If it's an acronym, return uppercase
  if (acronyms.includes(lowerUsername)) {
    return username.toUpperCase()
  }

  // For other usernames, capitalize first letter of each word
  // Handle underscores: "maintenance_officer" -> "Maintenance Officer"
  return username
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

