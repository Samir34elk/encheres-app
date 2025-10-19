import { describe, it, expect } from 'vitest'

// Utility functions for validation
const isValidEmail = (email: string): boolean => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

const isValidPassword = (password: string): boolean => {
  return password.length >= 8
}

const isValidUsername = (username: string): boolean => {
  return username.length >= 3 && username.length <= 20
}

describe('Validation Utilities', () => {
  describe('isValidEmail', () => {
    it('should validate correct email addresses', () => {
      expect(isValidEmail('test@example.com')).toBe(true)
      expect(isValidEmail('user.name@domain.co.uk')).toBe(true)
      expect(isValidEmail('user+tag@example.com')).toBe(true)
    })

    it('should reject invalid email addresses', () => {
      expect(isValidEmail('invalid')).toBe(false)
      expect(isValidEmail('invalid@')).toBe(false)
      expect(isValidEmail('@example.com')).toBe(false)
      expect(isValidEmail('test@.com')).toBe(false)
      expect(isValidEmail('')).toBe(false)
    })
  })

  describe('isValidPassword', () => {
    it('should validate passwords with minimum length', () => {
      expect(isValidPassword('12345678')).toBe(true)
      expect(isValidPassword('longpassword')).toBe(true)
    })

    it('should reject short passwords', () => {
      expect(isValidPassword('short')).toBe(false)
      expect(isValidPassword('1234567')).toBe(false)
      expect(isValidPassword('')).toBe(false)
    })
  })

  describe('isValidUsername', () => {
    it('should validate usernames within range', () => {
      expect(isValidUsername('user')).toBe(true)
      expect(isValidUsername('testuser')).toBe(true)
      expect(isValidUsername('username123')).toBe(true)
    })

    it('should reject usernames outside range', () => {
      expect(isValidUsername('ab')).toBe(false)
      expect(isValidUsername('verylongusernamethatexceedslimit')).toBe(false)
      expect(isValidUsername('')).toBe(false)
    })
  })
})
