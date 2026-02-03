import { cloneDeep } from 'lodash'

import { AskResponse, Citation } from '../../api'

export type ParsedAnswer = {
  citations: Citation[]
  markdownFormatText: string
}

export const enumerateCitations = (citations: Citation[]) => {
  const filepathMap = new Map()
  for (const citation of citations) {
    const { filepath } = citation
    let part_i = 1
    if (filepathMap.has(filepath)) {
      part_i = filepathMap.get(filepath) + 1
    }
    filepathMap.set(filepath, part_i)
    citation.part_index = part_i
  }
  return citations
}

export function parseAnswer(answer: AskResponse): ParsedAnswer {
  let answerText = answer.answer
  
  const citationMarkerRegex = /\[\d+\]/g;
  // Early return if no citations available
  if (!answer.citations?.length) {
    return {
      citations: [],
      markdownFormatText: answerText.replace(citationMarkerRegex, '')
    }
  }

  // Extract unique citation markers and process them
  const citationMarkers = [...new Set(answerText.match(citationMarkerRegex) || [])]
  const processedCitations: Citation[] = []
  
  citationMarkers.forEach((marker, index) => {
    const citationIndex = parseInt(marker.slice(1, -1)) - 1 // Convert to 0-based index
    const citation = answer.citations[citationIndex]
    
    if (citation) {
      // Replace all instances of this marker with the new citation number
      const newCitationNumber = index + 1
      answerText = answerText.replaceAll(marker, ` ^${newCitationNumber}^ `)
      
      processedCitations.push({
        ...cloneDeep(citation),
        reindex_id: newCitationNumber.toString()
      })
    } else {
      // Remove invalid citation markers
      answerText = answerText.replaceAll(marker, '')
    }
  })
  
  return {
    citations: enumerateCitations(processedCitations),
    markdownFormatText: answerText
  }
}
