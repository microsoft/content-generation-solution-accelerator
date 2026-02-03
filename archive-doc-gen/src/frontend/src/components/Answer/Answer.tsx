import { FormEvent, useContext, useEffect, useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Components } from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { nord } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Checkbox, DefaultButton, Dialog, FontIcon, Stack, Text, Spinner, MessageBar, MessageBarType, PrimaryButton } from '@fluentui/react'
import { useBoolean } from '@fluentui/react-hooks'
import { ThumbDislike20Filled, ThumbLike20Filled } from '@fluentui/react-icons'
import DOMPurify from 'dompurify'
import remarkGfm from 'remark-gfm'
import supersub from 'remark-supersub'
import { AskResponse, Citation, Feedback, historyMessageFeedback } from '../../api'
import { XSSAllowTags } from '../../constants/xssAllowTags'
import { AppStateContext } from '../../state/AppProvider'

import { parseAnswer } from './AnswerParser'

import styles from './Answer.module.css'

interface Props {
  answer: AskResponse
  onCitationClicked: (citedDocument: Citation) => void
}

// Add interface for citation content response
interface CitationContentResponse {
  content: string
  title: string
  error?: string
}

export const Answer = ({ answer, onCitationClicked }: Props) => {
  const initializeAnswerFeedback = (answer: AskResponse) => {
    if (answer.message_id == undefined) return undefined
    if (answer.feedback == undefined) return undefined
    if (answer.feedback.split(',').length > 1) return Feedback.Negative
    if (Object.values(Feedback).includes(answer.feedback)) return answer.feedback
    return Feedback.Neutral
  }

  const [isRefAccordionOpen, { toggle: toggleIsRefAccordionOpen }] = useBoolean(false)

  const parsedAnswer = useMemo(() => parseAnswer(answer), [answer])
  const [chevronIsExpanded, setChevronIsExpanded] = useState(isRefAccordionOpen)
  const [feedbackState, setFeedbackState] = useState(initializeAnswerFeedback(answer))
  const [isFeedbackDialogOpen, setIsFeedbackDialogOpen] = useState(false)
  const [showReportInappropriateFeedback, setShowReportInappropriateFeedback] = useState(false)
  const [negativeFeedbackList, setNegativeFeedbackList] = useState<Feedback[]>([])
  
  // Add new state for citation content dialog
  const [isCitationContentDialogOpen, setIsCitationContentDialogOpen] = useState(false)
  const [citationContent, setCitationContent] = useState<CitationContentResponse | null>(null)
  const [isLoadingCitationContent, setIsLoadingCitationContent] = useState(false)
  const [citationContentError, setCitationContentError] = useState<string | null>(null)

  const appStateContext = useContext(AppStateContext)
  const FEEDBACK_ENABLED =
    appStateContext?.state.frontendSettings?.feedback_enabled && appStateContext?.state.isCosmosDBAvailable?.cosmosDB
  const SANITIZE_ANSWER = appStateContext?.state.frontendSettings?.sanitize_answer

  // Add function to fetch citation content
  const fetchCitationContent = async (citation: Citation) => {
    setIsLoadingCitationContent(true)
    setCitationContentError(null)
    
    try {
      const payload = {
        url: citation.url || '',
        title: citation.title || 'Citation Content',
      }

      const response = await fetch('/fetch-azure-search-content', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: CitationContentResponse = await response.json()
      // {
      //   content: "abcd",
      //   title: 'abcdtile'
      // } 
      setCitationContent(data)
      setIsCitationContentDialogOpen(true)
    } catch (error) {
      console.error('Error fetching citation content:', error)
      setCitationContentError(error instanceof Error ? error.message : 'Failed to fetch citation content')
    } finally {
      setIsLoadingCitationContent(false)
    }
  }

  // Update the onCitationClicked handler
  const handleCitationClick = (citation: Citation) => {
    // Call the original onCitationClicked prop
    onCitationClicked(citation)
    
    // Fetch citation content and show dialog
    fetchCitationContent(citation)
  }

  // Add function to close citation content dialog
  const closeCitationContentDialog = () => {
    setIsCitationContentDialogOpen(false)
    setCitationContent(null)
    setCitationContentError(null)
  }

  const handleChevronClick = () => {
    setChevronIsExpanded(!chevronIsExpanded)
    toggleIsRefAccordionOpen()
  }

  useEffect(() => {
    setChevronIsExpanded(isRefAccordionOpen)
  }, [isRefAccordionOpen])

  useEffect(() => {
    if (answer.message_id == undefined) return

    let currentFeedbackState
    if (appStateContext?.state.feedbackState && appStateContext?.state.feedbackState[answer.message_id]) {
      currentFeedbackState = appStateContext?.state.feedbackState[answer.message_id]
    } else {
      currentFeedbackState = initializeAnswerFeedback(answer)
    }
    setFeedbackState(currentFeedbackState)
  }, [appStateContext?.state.feedbackState, feedbackState, answer.message_id])

  const createCitationFilepath = (citation: Citation, index: number, truncate: boolean = false) => {
    // let citationFilename = ''
    // console.log('createCitationFilepath', citation, index, truncate)      
    // if (citation.filepath) {
    //   const part_i = citation.part_index ?? (citation.chunk_id ? parseInt(citation.chunk_id) + 1 : '')
    //   if (truncate && citation.filepath.length > filePathTruncationLimit) {
    //     const citationLength = citation.filepath.length
    //     citationFilename = `${citation.filepath.substring(0, 20)}...${citation.filepath.substring(citationLength - 20)} - Part ${part_i}`
    //   } else {
    //     citationFilename = `${citation.filepath} - Part ${part_i}`
    //   }
    // } else if (citation.filepath && citation.reindex_id) {
    //   citationFilename = `${citation.filepath} - Part ${citation.reindex_id}`
    // } else {
    //   citationFilename = `Citation ${index}`
    // }
    return citation.title ? citation.title : `Citation ${index + 1}`
  }

  const onLikeResponseClicked = async () => {
    if (answer.message_id == undefined) return

    let newFeedbackState: Feedback.Neutral | Feedback.Positive
    // Set or unset the thumbs up state
    if (feedbackState == Feedback.Positive) {
      newFeedbackState = Feedback.Neutral
    } else {
      newFeedbackState = Feedback.Positive
    }
    appStateContext?.dispatch({
      type: 'SET_FEEDBACK_STATE',
      payload: { answerId: answer.message_id, feedback: newFeedbackState }
    })
    setFeedbackState(newFeedbackState)

    // Update message feedback in db
    await historyMessageFeedback(answer.message_id, newFeedbackState)
  }

  const onDislikeResponseClicked = async () => {
    if (answer.message_id == undefined) return

    let newFeedbackState: Feedback.Neutral | Feedback.Negative
    if (feedbackState === undefined || feedbackState === Feedback.Neutral || feedbackState === Feedback.Positive) {
      newFeedbackState = Feedback.Negative
      setFeedbackState(newFeedbackState)
      setIsFeedbackDialogOpen(true)
    } else {
      // Reset negative feedback to neutral
      newFeedbackState = Feedback.Neutral
      setFeedbackState(newFeedbackState)
      await historyMessageFeedback(answer.message_id, Feedback.Neutral)
    }
    appStateContext?.dispatch({
      type: 'SET_FEEDBACK_STATE',
      payload: { answerId: answer.message_id, feedback: newFeedbackState }
    })
  }

  const updateFeedbackList = (ev?: FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
    if (answer.message_id == undefined) return
    const selectedFeedback = (ev?.target as HTMLInputElement)?.id as Feedback

    let feedbackList = negativeFeedbackList.slice()
    if (checked) {
      feedbackList.push(selectedFeedback)
    } else {
      feedbackList = feedbackList.filter(f => f !== selectedFeedback)
    }

    setNegativeFeedbackList(feedbackList)
  }

  const onSubmitNegativeFeedback = async () => {
    if (answer.message_id == undefined) return
    await historyMessageFeedback(answer.message_id, negativeFeedbackList.join(','))
    resetFeedbackDialog()
  }

  const resetFeedbackDialog = () => {
    setIsFeedbackDialogOpen(false)
    setShowReportInappropriateFeedback(false)
    setNegativeFeedbackList([])
  }

  const UnhelpfulFeedbackContent = () => {
    return (
      <>
        <div>Why wasn't this response helpful?</div>
        <Stack tokens={{ childrenGap: 4 }}>
          <Checkbox
            label="Citations are missing"
            id={Feedback.MissingCitation}
            defaultChecked={negativeFeedbackList.includes(Feedback.MissingCitation)}
            onChange={updateFeedbackList}></Checkbox>
          <Checkbox
            label="Citations are wrong"
            id={Feedback.WrongCitation}
            defaultChecked={negativeFeedbackList.includes(Feedback.WrongCitation)}
            onChange={updateFeedbackList}></Checkbox>
          <Checkbox
            label="The response is not from my data"
            id={Feedback.OutOfScope}
            defaultChecked={negativeFeedbackList.includes(Feedback.OutOfScope)}
            onChange={updateFeedbackList}></Checkbox>
          <Checkbox
            label="Inaccurate or irrelevant"
            id={Feedback.InaccurateOrIrrelevant}
            defaultChecked={negativeFeedbackList.includes(Feedback.InaccurateOrIrrelevant)}
            onChange={updateFeedbackList}></Checkbox>
          <Checkbox
            label="Other"
            id={Feedback.OtherUnhelpful}
            defaultChecked={negativeFeedbackList.includes(Feedback.OtherUnhelpful)}
            onChange={updateFeedbackList}></Checkbox>
        </Stack>
        <div data-testid="InappropriateFeedback" onClick={() => setShowReportInappropriateFeedback(true)} style={{ color: '#115EA3', cursor: 'pointer' }}>
          Report inappropriate content
        </div>
      </>
    )
  }

  const ReportInappropriateFeedbackContent = () => {
    return (
      <>
        <div data-testid="ReportInappropriateFeedbackContent">
          The content is <span style={{ color: 'red' }}>*</span>
        </div>
        <Stack tokens={{ childrenGap: 4 }}>
          <Checkbox
            label="Hate speech, stereotyping, demeaning"
            id={Feedback.HateSpeech}
            defaultChecked={negativeFeedbackList.includes(Feedback.HateSpeech)}
            onChange={updateFeedbackList}></Checkbox>
          <Checkbox
            label="Violent: glorification of violence, self-harm"
            id={Feedback.Violent}
            defaultChecked={negativeFeedbackList.includes(Feedback.Violent)}
            onChange={updateFeedbackList}></Checkbox>
          <Checkbox
            label="Sexual: explicit content, grooming"
            id={Feedback.Sexual}
            defaultChecked={negativeFeedbackList.includes(Feedback.Sexual)}
            onChange={updateFeedbackList}></Checkbox>
          <Checkbox
            label="Manipulative: devious, emotional, pushy, bullying"
            defaultChecked={negativeFeedbackList.includes(Feedback.Manipulative)}
            id={Feedback.Manipulative}
            onChange={updateFeedbackList}></Checkbox>
          <Checkbox
            label="Other"
            id={Feedback.OtherHarmful}
            defaultChecked={negativeFeedbackList.includes(Feedback.OtherHarmful)}
            onChange={updateFeedbackList}></Checkbox>
        </Stack>
      </>
    )
  }

  const components: Components = {
    a: ({ href, children, ...props }) => (
      <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
        {children}
      </a>
    ),
    code({ inline, className, children, ...props }: { 
      inline?: boolean; 
      className?: string; 
      children?: React.ReactNode; 
      [key: string]: any 
    }) {
      const match = /language-(\w+)/.exec(className || '');
      // Handle inline and block code rendering
      if (inline) {
        return (
          <code className={className} {...props}>
            {children}
          </code>
        );
      } else if (match) {
        return (
          <SyntaxHighlighter
            style={nord}
            language={match[1]}
            PreTag="div"
            {...props}
          >
            {String(children).replace(/\n$/, '')}
          </SyntaxHighlighter>
        );
      }
    }
  }
  return (
    <>
      <Stack className={styles.answerContainer} tabIndex={0}>
        <Stack.Item>
          <Stack horizontal grow>
            <Stack.Item grow>
            <div className={styles.answerText}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm, supersub]}
                children={
                  SANITIZE_ANSWER
                    ? DOMPurify.sanitize(parsedAnswer.markdownFormatText, { ALLOWED_TAGS: XSSAllowTags })
                    : parsedAnswer.markdownFormatText
                }
                components={components}
              />
              </div>
            </Stack.Item>
            <Stack.Item className={styles.answerHeader}>
              {FEEDBACK_ENABLED && answer.message_id !== undefined && (
                <Stack horizontal horizontalAlign="space-between">
                  <ThumbLike20Filled
                    aria-hidden="false"
                    aria-label="Like this response"
                    onClick={() => onLikeResponseClicked()}
                    style={
                      feedbackState === Feedback.Positive ||
                      appStateContext?.state.feedbackState[answer.message_id] === Feedback.Positive
                        ? { color: 'darkgreen', cursor: 'pointer' }
                        : { color: 'slategray', cursor: 'pointer' }
                    }
                  />
                  <ThumbDislike20Filled
                    aria-hidden="false"
                    aria-label="Dislike this response"
                    onClick={() => onDislikeResponseClicked()}
                    style={
                      feedbackState !== Feedback.Positive &&
                      feedbackState !== Feedback.Neutral &&
                      feedbackState !== undefined
                        ? { color: 'darkred', cursor: 'pointer' }
                        : { color: 'slategray', cursor: 'pointer' }
                    }
                  />
                </Stack>
              )}
            </Stack.Item>
          </Stack>
        </Stack.Item>
        <Stack horizontal className={styles.answerFooter}>
          {!!parsedAnswer.citations.length && (
            <Stack.Item data-testid="stack-item" onKeyDown={e => (e.key === 'Enter' || e.key === ' ' ? toggleIsRefAccordionOpen() : null)}>
              <Stack style={{ width: '100%' }}>
                <Stack horizontal horizontalAlign="start" verticalAlign="center">
                  <Text
                    className={styles.accordionTitle}
                    onClick={toggleIsRefAccordionOpen}
                    aria-label="Open references"
                    tabIndex={0}
                    role="button">
                    <span>
                      {parsedAnswer.citations.length > 1
                        ? parsedAnswer.citations.length + ' references'
                        : '1 reference'}
                    </span>
                  </Text>
                  <FontIcon
                    data-testid="ChevronIcon"
                    className={styles.accordionIcon}
                    onClick={handleChevronClick}
                    iconName={chevronIsExpanded ? 'ChevronDown' : 'ChevronRight'}
                  />
                </Stack>
              </Stack>
            </Stack.Item>
          )}
          <Stack.Item className={styles.answerDisclaimerContainer}>
            <span className={styles.answerDisclaimer}>AI-generated content may be incorrect</span>
          </Stack.Item>
        </Stack>
        {chevronIsExpanded && (
          <div className={styles.citationWrapper}>
            {parsedAnswer.citations.map((citation, idx) => {
              return (
                <span
                  title={citation.title ?? undefined}
                  tabIndex={0}
                  role="link"
                  key={idx}
                  onClick={() => handleCitationClick(citation)}
                  onKeyDown={e => (e.key === 'Enter' || e.key === ' ' ? handleCitationClick(citation) : null)}
                  className={styles.citationContainer}
                  aria-label={createCitationFilepath(citation, idx)}>
                  <div className={styles.citation}>{idx+1}</div>
                  {createCitationFilepath(citation, idx, true)}
                </span>
              )
            })}
          </div>
        )}
      </Stack>

      {/* Existing feedback dialog */}
      <Dialog
        onDismiss={() => {
          resetFeedbackDialog()
          setFeedbackState(Feedback.Neutral)
        }}
        hidden={!isFeedbackDialogOpen}
        styles={{
          main: [
            {
              selectors: {
                ['@media (min-width: 480px)']: {
                  maxWidth: '600px',
                  background: '#FFFFFF',
                  boxShadow: '0px 14px 28.8px rgba(0, 0, 0, 0.24), 0px 0px 8px rgba(0, 0, 0, 0.2)',
                  borderRadius: '8px',
                  maxHeight: '600px',
                  minHeight: '100px'
                }
              }
            }
          ]
        }}
        dialogContentProps={{
          title: 'Submit Feedback',
          showCloseButton: true
        }}>
        <Stack tokens={{ childrenGap: 4 }}>
          <div>Your feedback will improve this experience.</div>
          {!showReportInappropriateFeedback ? <UnhelpfulFeedbackContent /> : <ReportInappropriateFeedbackContent />}
          <div>By pressing submit, your feedback will be visible to the application owner.</div>
          <DefaultButton disabled={negativeFeedbackList.length < 1} onClick={onSubmitNegativeFeedback}>
            Submit
          </DefaultButton>
        </Stack>
      </Dialog>


  {isLoadingCitationContent && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '8px',
            boxShadow: '0px 14px 28.8px rgba(0, 0, 0, 0.24)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '16px'
          }}>
            <Spinner size={3} />
            <Text>Loading citation content...</Text>
          </div>
        </div>
      )}
      {/* New citation content dialog */}
      <Dialog
        onDismiss={closeCitationContentDialog}
        hidden={!isCitationContentDialogOpen}
        styles={{
          main: [
            {
              selectors: {
                ['@media (min-width: 480px)']: {
                  width: '800px',
                  height: '600px',
                  maxWidth: '800px',
                  maxHeight: '600px',
                  minWidth: '800px',
                  minHeight: '600px',
                  background: '#FFFFFF',
                  boxShadow: '0px 14px 28.8px rgba(0, 0, 0, 0.24), 0px 0px 8px rgba(0, 0, 0, 0.2)',
                  borderRadius: '8px'
                }
              }
            }
          ]
        }}
        dialogContentProps={{
          title: citationContent?.title || 'Citation Content',
          showCloseButton: true
        }}>
        <Stack tokens={{ childrenGap: 16 }} styles={{ root: { height: '500px' } }}>
          {isLoadingCitationContent && (
            <Stack horizontal horizontalAlign="center" tokens={{ childrenGap: 8 }}>
              <Spinner label="Loading citation content..." />
            </Stack>
          )}
          
          {citationContentError && (
            <MessageBar messageBarType={MessageBarType.error}>
              Error loading citation content: {citationContentError}
            </MessageBar>
          )}
          
          {citationContent && !isLoadingCitationContent && (
            <div style={{ 
              height: '400px',
              overflowY: 'auto', 
              padding: '16px',
              border: '1px solid #e1e1e1',
              borderRadius: '4px',
              backgroundColor: '#fafafa'
            }}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm, supersub]}
                children={citationContent.content}
                components={components}
              />
            </div>
          )}
          
          <Stack horizontal horizontalAlign="end">
            <PrimaryButton onClick={closeCitationContentDialog}>
              Close
            </PrimaryButton>
          </Stack>
        </Stack>
      </Dialog>
    </>
  )
}
