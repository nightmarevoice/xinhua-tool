import React from 'react'
import { Layout } from 'antd'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'
import { Outlet } from 'react-router-dom'

const { Content } = Layout

const MainLayout: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar />
      <Layout style={{ marginLeft: 200 }}>
        <Header />
        <Content 
          className="mt-16 p-6 bg-gray-50 min-h-screen overflow-auto"
          style={{ 
            marginTop: 64,
            padding: '24px',
            background: '#f0f2f5',
            minHeight: 'calc(100vh - 64px)',
            overflow: 'auto'
          }}
        >
          <div className="bg-white p-6 rounded-lg shadow-sm" style={{height:'100%'}}>
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout














