import {
  Card,
  Text,
  tokens,
} from '@fluentui/react-components';
import FirstPromptIcon from '../styles/images/firstprompt.png';
import SecondPromptIcon from '../styles/images/secondprompt.png';

interface SuggestionCard {
  title: string;
  prompt: string;
  icon: string;
}

const suggestions: SuggestionCard[] = [
  {
    title: "I need to create a social media post about paint products for home remodels. The campaign is titled \"Brighten Your Springtime\" and the audience is new homeowners. I need marketing copy plus an image. The image should be an informal living room with tasteful furnishings.",
    prompt: "I need to create a social media post about paint products for home remodels. The campaign is titled \"Brighten Your Springtime\" and the audience is new homeowners. I need marketing copy plus an image. The image should be an informal living room with tasteful furnishings.",
    icon: FirstPromptIcon,
  },
  {
    title: "Generate a social media campaign with ad copy and an image. This is for \"Back to School\" and the audience is parents of school age children. Tone is playful and humorous. The image must have minimal kids accessories in a children's bedroom. Show the room in a wide view.",
    prompt: "Generate a social media campaign with ad copy and an image. This is for \"Back to School\" and the audience is parents of school age children. Tone is playful and humorous. The image must have minimal kids accessories in a children's bedroom. Show the room in a wide view.",
    icon: SecondPromptIcon,
  }
];

interface WelcomeCardProps {
  onSuggestionClick: (prompt: string) => void;
  currentInput?: string;
}

export function WelcomeCard({ onSuggestionClick, currentInput = '' }: WelcomeCardProps) {
  const selectedIndex = suggestions.findIndex(s => s.prompt === currentInput);
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
            <Card
              key={index}
              onClick={() => onSuggestionClick(suggestion.prompt)}
              style={{
                padding: 'clamp(12px, 2vw, 16px)',
                cursor: 'pointer',
                backgroundColor: isSelected ? tokens.colorBrandBackground2 : tokens.colorNeutralBackground1,
                border: 'none',
                borderRadius: '16px',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.backgroundColor = tokens.colorBrandBackground2;
                }
              }}
              onMouseLeave={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.backgroundColor = tokens.colorNeutralBackground1;
                }
              }}
            >
              <div style={{ 
                display: 'flex',
                alignItems: 'center',
                gap: 'clamp(8px, 1.5vw, 12px)',
              }}>
                <div style={{ 
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 'clamp(32px, 5vw, 40px)',
                  height: 'clamp(32px, 5vw, 40px)',
                  minWidth: '32px',
                  minHeight: '32px',
                  flexShrink: 0,
                }}>
                  <img 
                    src={suggestion.icon} 
                    alt="Prompt icon" 
                    style={{ 
                      width: '100%', 
                      height: '100%', 
                      objectFit: 'contain' 
                    }} 
                  />
                </div>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <Text 
                    size={300} 
                    block 
                    style={{ 
                      fontSize: 'clamp(13px, 1.8vw, 15px)',
                    }}
                  >
                    {suggestion.title}
                  </Text>
                </div>
              </div>
            </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
