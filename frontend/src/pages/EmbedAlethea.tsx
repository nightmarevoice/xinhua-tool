import React from 'react'
import { Button, Space, Tooltip } from 'antd'
import { LinkOutlined, ReloadOutlined } from '@ant-design/icons'

const PROXY_BASE = '/proxy/alethea/'
const DIRECT_URL = 'https://www.alethea.ai/?utm_source=moge.ai'

const EmbedAlethea: React.FC = () => {
  const [reloadKey, setReloadKey] = React.useState(0)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 16, fontWeight: 600 }}>Alethea AI（通过内置代理）</div>
        <Space>
          <Tooltip title="在新标签页打开官网">
            <Button type="default" icon={<LinkOutlined />} href={DIRECT_URL} target="_blank" rel="noreferrer">
              打开官网
            </Button>
          </Tooltip>
          <Tooltip title="重新加载">
            <Button icon={<ReloadOutlined />} onClick={() => setReloadKey(v => v + 1)} />
          </Tooltip>
        </Space>
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        <iframe
          key={reloadKey}
          title="Alethea AI (proxied)"
          src={PROXY_BASE}
          style={{
            border: 0,
            width: '100%',
            height: '100%',
            borderRadius: 6,
            background: '#fff'
          }}
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
        />
      </div>
    </div>
  )
}

export default EmbedAlethea


