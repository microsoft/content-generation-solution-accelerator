import { memo, useMemo } from 'react';
import {
  Text,
  tokens,
} from '@fluentui/react-components';
import { SuggestionCard } from './SuggestionCard';
import FirstPromptIcon from '../styles/images/firstprompt.png';
import SecondPromptIcon from '../styles/images/secondprompt.png';

interface SuggestionData {
  title: string;
  icon: string;
}

const suggestions: SuggestionData[] = [
  {
    title: "I need to create a social media post about paint products for home remodels. The campaign is titled \"Brighten Your Springtime\" and the audience is new homeowners. I need marketing copy plus an image. The image should be an informal living room with tasteful furnishings.",
    icon: FirstPromptIcon,
  },
  {
    title: "Generate a social media campaign with ad copy and an image. This is for \"Back to School\" and the audience is parents of school age children. Tone is playful and humorous. The image must have minimal kids accessories in a children's bedroom. Show the room in a wide view.",
    icon: SecondPromptIcon,
  }
];

interface WelcomeCardProps {
  onSuggestionClick: (prompt: string) => void;
  currentInput?: string;
}

export const WelcomeCard = memo(function WelcomeCard({ onSuggestionClick, currentInput = '' }: WelcomeCardProps) {
  const selectedIndex = useMemo(
    () => suggestions.findIndex(s => s.title === currentInput),
    [currentInput],
  );

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      flex: 1,
      padding: 'clamp(16px, 4vw, 32px)',
      gap: 'clamp(16px, 3vw, 24px)',
      width: '100%',
      boxSizing: 'border-box',
    }}>
      {/* Welcome card with suggestions inside */}
      <div style={{
        padding: 'clamp(16px, 4vw, 32px)',
        maxWidth: 'min(600px, 100%)',
        width: '100%',
        backgroundColor: tokens.colorNeutralBackground3,
        borderRadius: '12px',
        boxSizing: 'border-box',
      }}>
        {/* Header with icon and welcome message */}
        <div style={{ textAlign: 'center', marginBottom: 'clamp(16px, 3vw, 24px)' }}>
          <Text 
            size={400} 
            weight="semibold" 
            block 
            style={{ 
              marginBottom: '8px', 
              textAlign: 'center',
              fontSize: 'clamp(16px, 2.5vw, 20px)',
            }}
          >
            Welcome to your Content Generation Accelerator
          </Text>
          <Text 
            size={300} 
            style={{ 
              color: tokens.colorNeutralForeground3, 
              display: 'block', 
              textAlign: 'center',
              fontSize: 'clamp(13px, 2vw, 15px)',
            }}
          >
            Here are the options I can assist you with today
          </Text>
        </div>
        
        {/* Suggestion cards - vertical layout */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'clamp(8px, 1.5vw, 12px)',
        }}>
          {suggestions.map((suggestion, index) => {
            const isSelected = index === selectedIndex;
            return (
            <SuggestionCard
              key={index}
              title={suggestion.title}
              icon={suggestion.icon}
              isSelected={isSelected}
              onClick={() => onSuggestionClick(suggestion.title)}
            />
            );
          })}
        </div>
      </div>
    </div>
  );
});
WelcomeCard.displayName = 'WelcomeCard';
