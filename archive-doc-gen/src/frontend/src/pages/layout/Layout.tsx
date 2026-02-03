import { useContext, useEffect, useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { Dialog, Stack, TextField } from '@fluentui/react'
import { CopyRegular } from '@fluentui/react-icons'

import { CosmosDBStatus, Conversation, historyList, ChatHistoryLoadingState } from '../../api'
import Contoso from '../../assets/Contoso.svg'
import { HistoryButton, ShareButton } from '../../components/common/Button'
import { AppStateContext } from '../../state/AppProvider'
import styles from './Layout.module.css'
import Sidebar from '../../components/Sidebar/Sidebar'


const Layout = () => {
  const location = useLocation();
  const [isSharePanelOpen, setIsSharePanelOpen] = useState<boolean>(false)
  const [copyClicked, setCopyClicked] = useState<boolean>(false)
  const [copyText, setCopyText] = useState<string>('Copy URL')
  const [shareLabel, setShareLabel] = useState<string | undefined>('Share')
  const [hideHistoryLabel, setHideHistoryLabel] = useState<string>('Hide template history')
  const [showHistoryLabel, setShowHistoryLabel] = useState<string>('Show template history')
  const appStateContext = useContext(AppStateContext)
  const ui = appStateContext?.state.frontendSettings?.ui

  const handleShareClick = () => {
    setIsSharePanelOpen(true)
  }

  const handleSharePanelDismiss = () => {
    setIsSharePanelOpen(false)
    setCopyClicked(false)
    setCopyText('Copy URL')
  }

  const handleCopyClick = () => {
    navigator.clipboard.writeText(window.location.href)
    setCopyClicked(true)
  }

  const handleHistoryClick = () => {
    appStateContext?.dispatch({ type: 'TOGGLE_CHAT_HISTORY' })
    
    // Fetch chat history if it's not already loaded
    if(!appStateContext?.state.chatHistory) {
      appStateContext?.dispatch({ type: 'UPDATE_CHAT_HISTORY_LOADING_STATE', payload: ChatHistoryLoadingState.Loading })    
      fetchChatHistory()
        .then(res => {
          if (res) {
            appStateContext?.dispatch({ type: 'UPDATE_CHAT_HISTORY_LOADING_STATE', payload: ChatHistoryLoadingState.Success })
          } else {
            appStateContext?.dispatch({ type: 'UPDATE_CHAT_HISTORY_LOADING_STATE', payload: ChatHistoryLoadingState.Fail })
            appStateContext?.dispatch({
              type: 'SET_COSMOSDB_STATUS',
              payload: { cosmosDB: false, status: CosmosDBStatus.NotWorking }
            })
          }
        })
        .catch(_err => {
          appStateContext?.dispatch({ type: 'UPDATE_CHAT_HISTORY_LOADING_STATE', payload: ChatHistoryLoadingState.Fail })
          appStateContext?.dispatch({
            type: 'SET_COSMOSDB_STATUS',
            payload: { cosmosDB: false, status: CosmosDBStatus.NotWorking }
          })
        })
    }
  }

  const fetchChatHistory = async (offset = 0): Promise<Conversation[] | null> => {
    const result = await historyList(offset)
      .then(response => {
        if (response) {
          appStateContext?.dispatch({ type: 'FETCH_CHAT_HISTORY', payload: response })
        } else {
          appStateContext?.dispatch({ type: 'FETCH_CHAT_HISTORY', payload: null })
        }
        return response
      })
      .catch(_err => {
        appStateContext?.dispatch({ type: 'UPDATE_CHAT_HISTORY_LOADING_STATE', payload: ChatHistoryLoadingState.Fail })
        appStateContext?.dispatch({ type: 'FETCH_CHAT_HISTORY', payload: null })
        console.error('There was an issue fetching your data.')
        return null
      })
    return result
  }

  useEffect(() => {
    if (copyClicked) {
      setCopyText('Copied URL')
    }
  }, [copyClicked])

  useEffect(() => {}, [appStateContext?.state.isCosmosDBAvailable.status])

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 480) {
        setShareLabel(undefined)
        setHideHistoryLabel('Hide history')
        setShowHistoryLabel('Show history')
      } else {
        setShareLabel('Share')
        setHideHistoryLabel('Hide template history')
        setShowHistoryLabel('Show template history')
      }
    }

    window.addEventListener('resize', handleResize)
    handleResize()

    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const shouldShowHistoryButton = location.pathname === '/generate'
  return (
    <div className={styles.layout}>
      <header className={styles.header} role={'banner'}>
        <Stack horizontal verticalAlign="center" horizontalAlign="space-between">
          <Stack horizontal verticalAlign="center">
            <img src={ui?.logo ? ui.logo : Contoso} className={styles.headerIcon} aria-hidden="true" alt="" />
            <Link to="/" className={styles.headerTitleContainer}>
              <h1 className={styles.headerTitle}>{ui?.title}</h1>
            </Link>
          </Stack>
          <Stack horizontal tokens={{ childrenGap: 4 }} className={styles.shareButtonContainer}>
            {shouldShowHistoryButton && appStateContext?.state.isCosmosDBAvailable?.status !== CosmosDBStatus.NotConfigured && (
              <HistoryButton
                onClick={handleHistoryClick}
                text={appStateContext?.state?.isChatHistoryOpen ? hideHistoryLabel : showHistoryLabel}
              />
            )}
            {ui?.show_share_button && <ShareButton onClick={handleShareClick} text={shareLabel} />}
          </Stack>
        </Stack>
      </header>

      <Stack 
        horizontal
        className={styles.layoutContainer}
      >
        <div className={styles.mainContainer} role="main">
          <Stack horizontal className={styles.outletRoot}>
            <div className={styles.outletContainer}>
              <div className={styles.childContainer}>
                <Outlet />
              </div>
              <Sidebar />
            </div>
          </Stack>
        </div>
      </Stack>
      
      <Dialog
        onDismiss={handleSharePanelDismiss}
        hidden={!isSharePanelOpen}
        styles={{
          main: [
            {
              selectors: {
                ['@media (min-width: 480px)']: {
                  maxWidth: '600px',
                  background: '#FFFFFF',
                  boxShadow: '0px 14px 28.8px rgba(0, 0, 0, 0.24), 0px 0px 8px rgba(0, 0, 0, 0.2)',
                  borderRadius: '8px',
                  maxHeight: '200px',
                  minHeight: '100px'
                }
              }
            }
          ]
        }}
        dialogContentProps={{
          title: 'Share the web app',
          showCloseButton: true
        }}>
        <Stack horizontal verticalAlign="center" style={{ gap: '8px' }}>
          <TextField className={styles.urlTextBox} defaultValue={window.location.href} readOnly />
          <div
            className={styles.copyButtonContainer}
            role="button"
            tabIndex={0}
            aria-label="Copy"
            onClick={handleCopyClick}
            onKeyDown={e => (e.key === 'Enter' || e.key === ' ' ? handleCopyClick() : null)}>
            <CopyRegular className={styles.copyButton} />
            <span className={styles.copyButtonText}>{copyText}</span>
          </div>
        </Stack>
      </Dialog>
    </div>
  )
}

export default Layout
