// __mocks__/react-markdown.tsx

import React from 'react';

const ReactMarkdown: React.FC<{ children: React.ReactNode , components: any }> = ({ children,components }) => {
  return <div data-testid="reactMockDown">
    {/* {components && components.code({ node: { children: [{ value: 'console.log("Test Code");' }] }, ...mockProps })} */}
    {children}</div>; // Simply render the children
};

export default ReactMarkdown;
