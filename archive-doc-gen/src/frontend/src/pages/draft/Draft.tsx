import { useContext, useEffect, useMemo, useState } from 'react'
import styles from './Draft.module.css'
import { useNavigate } from 'react-router-dom'
import TitleCard from '../../components/DraftCards/TitleCard'
import SectionCard from '../../components/DraftCards/SectionCard'
import { Document, Packer, Paragraph, TextRun } from 'docx'
import { saveAs } from 'file-saver'
import { AppStateContext } from '../../state/AppProvider'
import { CommandBarButton, Stack } from '@fluentui/react';
import { Section } from '../../api/models'

const Draft = (): JSX.Element => {
  const appStateContext = useContext(AppStateContext)
  const navigate = useNavigate()

  // get draftedDocument from context
  const draftedDocument = appStateContext?.state.draftedDocument
  const currentChat = appStateContext?.state.currentChat
  const draftedDocumentTitle = appStateContext?.state.draftedDocumentTitle;
  const sections = draftedDocument?.sections ?? []

  const isLoadedSections = appStateContext?.state.isLoadedSections


  const [sectionItems, setSectionItems] = useState<Section[]>([])
  const aiWarningLabel = 'AI-generated content may be incorrect'


  const [isExportButtonDisable, setIsExportButtonDisable] = useState<boolean>(false)

  useMemo(() => {
      currentChat?.title && appStateContext?.dispatch({ type: 'UPDATE_DRAFTED_DOCUMENT_TITLE', payload: currentChat.title })
  }, [currentChat?.title])

  useEffect(() => {
    sections.forEach((item, index) => {
      setTimeout(() => {
        setSectionItems((prev) => [...prev, item]);
      }, index * 500);
    });

    return () => {
      appStateContext?.dispatch({ type: 'UPDATE_IS_LOADED_SECTIONS', payload: { section: null, 'act': 'removeAll' } })
    }

  }, []);



  useEffect(() => {
    const title = draftedDocumentTitle ?? '' // Normalize null to ''
    if (isLoadedSections?.length === sections.length && title.length > 0) {
      setIsExportButtonDisable(false);
    }
    else {
      setIsExportButtonDisable(true);
    }
  }, [isLoadedSections, draftedDocumentTitle])


  if (!draftedDocument) {
    navigate('/')
  }

  const exportToWord = () => {
    const doc = new Document({
      sections: [
        {
          properties: {},
          children: [
            new Paragraph({
              children: [
                new TextRun({
                  text: getTitle(),
                  bold: true,
                  size: 24
                }),
                new TextRun({
                  text: '\n',
                  break: 1 // Add a new line after the title
                }),
                new TextRun({
                  text: aiWarningLabel,
                  size: 12
                }),
                new TextRun({
                  text: '\n',
                  break: 1 // Add a new line after the AI statement
                })
              ]
            }),
            ...sections.map(
              (section, index) =>
                new Paragraph({
                  children: [
                    new TextRun({
                      text: `Section ${index + 1}: ${section.title}`,
                      bold: true,
                      size: 20
                    }),
                    new TextRun({
                      text: '',
                      break: 1 // Add a new line after the section title
                    }),
                    ...section.content
                      .split('\n')
                      .map((line, lineIndex) => [
                        new TextRun({
                          text: line,
                          size: 16
                        }),
                        new TextRun({
                          text: '',
                          break: 1 // Add a new line after each line of content
                        })
                      ])
                      .flat()
                  ]
                })
            )
          ]
        }
      ]
    })

    Packer.toBlob(doc).then(blob => {
      saveAs(blob, `DraftTemplate-${sanitizeTitle(getTitle())}.docx`)
    })
  }

  function getTitle() {
    if (appStateContext === undefined) return ''
    return appStateContext.state.draftedDocumentTitle === null ? '' : appStateContext.state.draftedDocumentTitle
  }
  function sanitizeTitle(title: string): string {
    return title.replace(/[^a-zA-Z0-9]/g, '')
  }

  return (
    <Stack className={styles.container}>
      <TitleCard />
      {(sectionItems).map((_, index: any) => (
        <SectionCard key={index} sectionIdx={index} />
      ))}
      <Stack className={styles.buttonContainer}>
        <CommandBarButton
          role="button"
          styles={{
            icon: {
              color: '#FFFFFF'
            },
            iconDisabled: {
              color: '#BDBDBD !important'
            },
            root: {
              color: '#FFFFFF',
              background: '#1367CF'
            },
            rootDisabled: {
              background: '#F0F0F0'
            }
          }}
          className={styles.exportDocumentIcon}
          iconProps={{ iconName: 'WordDocument' }}
          onClick={exportToWord}
          aria-label="export document"
          text="Export Document"
          disabled={isExportButtonDisable}
        />
      </Stack>
    </Stack>
  )
}

export default Draft
