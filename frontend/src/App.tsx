import React from 'react'
import { useRoutes, Navigate } from 'react-router-dom'
import { routes } from './config/routes'

const App: React.FC = () => {
  const element = useRoutes([
    ...routes,
    { path: '*', element: <Navigate to="/" replace /> }
  ])

  return element
}

export default App
