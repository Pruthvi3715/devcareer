import React, { useState, useRef, useEffect, useContext } from 'react'
import { AuthContext } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

export default function ProfileIcon() {
  const { user, token, logout } = useContext(AuthContext)
  const [open, setOpen] = useState(false)
  const menuRef = useRef(null)
  const navigate = useNavigate()

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  if (!token) {
    return (
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={() => navigate('/login')}
          style={{
            padding: '6px 16px',
            fontSize: '14px',
            color: '#7c3aed',
            background: 'transparent',
            border: '1px solid #7c3aed',
            borderRadius: '8px',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseEnter={e => { e.target.style.background = '#7c3aed'; e.target.style.color = '#fff' }}
          onMouseLeave={e => { e.target.style.background = 'transparent'; e.target.style.color = '#7c3aed' }}
        >
          Login
        </button>
        <button
          onClick={() => navigate('/signup')}
          style={{
            padding: '6px 16px',
            fontSize: '14px',
            color: '#fff',
            background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          Sign Up
        </button>
      </div>
    )
  }

  const initial = user?.email ? user.email[0].toUpperCase() : '?'
  const displayName = user?.email?.split('@')[0] || 'User'

  return (
    <div ref={menuRef} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(!open)}
        aria-label="User profile menu"
        aria-expanded={open}
        style={{
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
          color: '#fff',
          border: 'none',
          cursor: 'pointer',
          fontSize: '15px',
          fontWeight: '700',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'box-shadow 0.2s',
          boxShadow: open ? '0 0 0 3px rgba(124,58,237,0.3)' : 'none',
        }}
      >
        {initial}
      </button>

      {open && (
        <div
          style={{
            position: 'absolute',
            top: '44px',
            right: '0',
            background: '#fff',
            borderRadius: '12px',
            boxShadow: '0 8px 30px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.08)',
            border: '1px solid #e5e7eb',
            minWidth: '200px',
            padding: '8px 0',
            zIndex: 100,
            animation: 'fadeInDown 0.15s ease-out',
          }}
        >
          {/* User info header */}
          <div style={{
            padding: '12px 16px',
            borderBottom: '1px solid #f3f4f6',
          }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#111827' }}>
              {displayName}
            </div>
            <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '2px' }}>
              {user?.email}
            </div>
          </div>

          {/* Menu items */}
          <button
            onClick={() => { setOpen(false); navigate('/profile') }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              width: '100%',
              padding: '10px 16px',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: '14px',
              color: '#374151',
              textAlign: 'left',
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => e.target.style.background = '#f9fafb'}
            onMouseLeave={e => e.target.style.background = 'none'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            My Profile
          </button>

          <button
            onClick={() => { setOpen(false); navigate('/') }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              width: '100%',
              padding: '10px 16px',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: '14px',
              color: '#374151',
              textAlign: 'left',
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => e.target.style.background = '#f9fafb'}
            onMouseLeave={e => e.target.style.background = 'none'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
            Home
          </button>

          <div style={{ height: '1px', background: '#f3f4f6', margin: '4px 0' }} />

          <button
            onClick={() => { setOpen(false); logout(); navigate('/') }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              width: '100%',
              padding: '10px 16px',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: '14px',
              color: '#ef4444',
              textAlign: 'left',
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => e.target.style.background = '#fef2f2'}
            onMouseLeave={e => e.target.style.background = 'none'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Logout
          </button>
        </div>
      )}
    </div>
  )
}
