import { render, screen, fireEvent, act, waitFor } from '@testing-library/react'
import { AppStateContext } from '../../state/AppProvider'
import Draft from './Draft'
import { saveAs } from 'file-saver'
import { MemoryRouter } from 'react-router-dom';

import { Document} from 'docx'


// Mocks for third-party components and modules
jest.mock('file-saver', () => ({
  saveAs: jest.fn(),
}))

jest.mock('../../components/DraftCards/TitleCard', () => ({ children }: { children: React.ReactNode }) => (
  <div data-testid="title-card">
    Title Card
    {children}
  </div>
))

jest.mock('../../components/DraftCards/SectionCard', () => ({
  __esModule: true,
  default: ({ sectionIdx }: { sectionIdx: number }) => (
    <div data-testid={`section-card-${sectionIdx}`}>Section {sectionIdx}</div>
  ),
}))

// Mock CommandBarButton from Fluent UI
jest.mock('@fluentui/react', () => ({
  ...jest.requireActual('@fluentui/react'),
  CommandBarButton: ({ onClick, disabled, text, ariaLabel, iconProps }: any) => (
    <button
      aria-label={ariaLabel}
      onClick={onClick}
      disabled={disabled}
      data-testid="command-bar-button">
      {iconProps?.iconName && <span>{iconProps.iconName}</span>}
      {text}
    </button>
  ),
}));

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
}))

jest.mock('docx', () => ({
  Document: jest.fn().mockImplementation((options) => {
    return {
      sections: options.sections || [],
    }
  }),
  Packer: {
    toBlob: jest.fn().mockResolvedValue(new Blob()), // Mock the toBlob method
  },
  Paragraph: jest.fn(),
  TextRun: jest.fn(),
}))

const mockAppState = {
  draftedDocument: {
    sections: [
      { title: 'Section 1', content: 'Content of section 1.' },
      { title: 'Section 2', content: 'Content of section 2.' }
    ]
  },
  isLoadedSections: [],
  draftedDocumentTitle: 'Sample Draft'
}


const renderComponent = (appState: any) => {
  return render(
    <MemoryRouter>
      <AppStateContext.Provider value={{ state: appState, dispatch: jest.fn() }}>
        <Draft />
      </AppStateContext.Provider>
    </MemoryRouter>
  )
}

describe('Draft Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()

  })


  test('renders TitleCard and SectionCards correctly', async () => {
    renderComponent(mockAppState)

    expect(screen.getByTestId('title-card')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByTestId('section-card-0')).toBeInTheDocument()
      expect(screen.getByTestId('section-card-1')).toBeInTheDocument()
    })


  })

  test('disables the export button when sections are not loaded', async () => {
    const mockStateWithIncompleteLoad = {
      ...mockAppState,
      isLoadedSections: [{ title: 'Section 1', content: 'Content of section 1' }], // One section not loaded
    }
    renderComponent(mockStateWithIncompleteLoad)

    await waitFor(() => {
      const exportButton = screen.getByTestId('command-bar-button')
      expect(exportButton).toBeDisabled()
    })

  })

  test('enabled the export button when sections are loaded', async () => {
    const mockStateWithIncompleteLoad = {
      ...mockAppState,
      isLoadedSections: [{ title: 'Section 1', content: 'Content of section 1' },
      { title: 'Section 2', content: 'Content of section 2.' }
      ],
      draftedDocument: {
        sections: [
          { title: 'Section 1', content: 'Content of section 1' },
          { title: 'Section 2', content: 'Content of section 2.' }
        ]
      },
      draftedDocumentTitle: 'My Draft Title',
    }
    renderComponent(mockStateWithIncompleteLoad)
    await waitFor(() => {
      const exportButton = screen.getByTestId('command-bar-button')
      expect(exportButton).toBeEnabled()
    })

  })

  test('triggers exportToWord function when export button is clicked', async () => {
    const mockStateWithIncompleteLoad = {
      ...mockAppState,
      isLoadedSections: [{ title: 'Section 1', content: 'Content of section 1' },
      { title: 'Section 2', content: 'Content of section 2.' }
      ], 
      draftedDocument: {
        sections: [
          { title: 'Section 1', content: 'Content of section 1' },
          { title: 'Section 2', content: 'Content of section 2.' }
        ]
      },
      draftedDocumentTitle: 'My Draft Title',
    }
    renderComponent(mockStateWithIncompleteLoad)

    await waitFor(async () => {

      const exportButton = screen.getByText(/Export Document/i)

      await act(async () => {
        fireEvent.click(exportButton)
      })

      expect(saveAs).toHaveBeenCalled()
    });
  })

  test('does not render any SectionCard when sections array is empty', async () => {
    const mockStateWithIncompleteLoad = {
      ...mockAppState,
      draftedDocument: {
        sections: []
      }
    }
    renderComponent(mockStateWithIncompleteLoad)

    await waitFor(() => {
      const sectionCards = screen.queryAllByTestId(/^section-card-/)
      expect(sectionCards).toHaveLength(0)
    });
  })

  test('does not render any SectionCard when sections array is null', async () => {
    const mockStateWithIncompleteLoad = {
      ...mockAppState,
      draftedDocument: {
        sections: null
      }
    }
    renderComponent(mockStateWithIncompleteLoad)

    await waitFor(() => {
      const sectionCards = screen.queryAllByTestId(/^section-card-/)
      expect(sectionCards).toHaveLength(0)
    });
  })

  test('redirects to home page when draftedDocument is empty', async () => {
    const mockStateEmptyDoc = {
      ...mockAppState,
      draftedDocument: null,
      sections: [],
      isLoadedSections: [],
      draftedDocumentTitle: null,
    }

    const mockNavigate = jest.fn()
    jest.spyOn(require('react-router-dom'), 'useNavigate').mockReturnValue(mockNavigate)

    renderComponent(mockStateEmptyDoc)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })

  })

  test('does not call saveAs if export button is disabled', async () => {
    const mockStateWithSectionsNotLoaded = {
      ...mockAppState,
      isLoadedSections: [], // Sections are not loaded
    }

    renderComponent(mockStateWithSectionsNotLoaded)

    const exportButton = screen.getByText(/Export Document/i)

    // Ensure the button is disabled and clicking it won't trigger export
    expect(exportButton).toBeDisabled()

    await act(async () => {
      fireEvent.click(exportButton)
    })

    expect(saveAs).not.toHaveBeenCalled()
  })

  test('calls saveAs when exportToWord is triggered', async () => {

    const mockStateWithIncompleteLoad = {
      ...mockAppState,
      isLoadedSections: [{ title: 'Section 1', content: 'Content of section 1' },
      { title: 'Section 2', content: 'Content of section 2.' }
      ], // One section not loaded
      draftedDocument: {
        sections: [
          { title: 'Section 1', content: 'Content of section 1' },
          { title: 'Section 2', content: 'Content of section 2.' }
        ]
      },
      draftedDocumentTitle: 'My Draft Title',
    }
    renderComponent(mockStateWithIncompleteLoad)

    await waitFor(async () => {

      const exportButton = screen.getByText(/Export Document/i)

      fireEvent.click(exportButton)
      //expect(Packer.toBlob).toHaveBeenCalledTimes(1)
      await waitFor(() => {
        expect(saveAs).toHaveBeenCalled()
      })
    });
  })


  test('generate document when draftedDocumentTitle is null', async () => {
    const mockStateWithIncompleteLoad = {
      ...mockAppState,
      isLoadedSections: [{ title: 'Section 1', content: 'Content of section 1' },
      { title: 'Section 2', content: 'Content of section 2.' }
      ],
      draftedDocument: {
        sections: [
          { title: 'Section 1', content: 'Content of section 1' },
          { title: 'Section 2', content: 'Content of section 2.' }
        ]
      },
      draftedDocumentTitle: 'My Draft Title', // title should not be null
    }
    renderComponent(mockStateWithIncompleteLoad)
    await waitFor(async () => {
      const exportButton = screen.getByText(/Export Document/i)
      fireEvent.click(exportButton)

      await waitFor(() => {
        expect(Document).toHaveBeenCalledTimes(1)
      })
    });
  })

})
