/**
 * Download the generated marketing image with a product-name / tagline
 * banner composited at the bottom.
 *
 * Falls back to a plain download when canvas compositing fails.
 */
export async function downloadImage(
  imageUrl: string,
  productName?: string,
  tagline?: string,
): Promise<void> {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = 'anonymous';

    img.onload = () => {
      const bannerHeight = Math.max(60, img.height * 0.1);
      const padding = Math.max(16, img.width * 0.03);

      canvas.width = img.width;
      canvas.height = img.height + bannerHeight;

      // Draw the image at the top
      ctx.drawImage(img, 0, 0);

      // White banner at the bottom
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, img.height, img.width, bannerHeight);

      ctx.strokeStyle = '#e5e5e5';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, img.height);
      ctx.lineTo(img.width, img.height);
      ctx.stroke();

      // Headline text
      const headlineText = productName || 'Your Product';
      const headlineFontSize = Math.max(18, Math.min(36, img.width * 0.04));
      const taglineFontSize = Math.max(12, Math.min(20, img.width * 0.025));

      ctx.font = `600 ${headlineFontSize}px Georgia, serif`;
      ctx.fillStyle = '#1a1a1a';
      ctx.fillText(
        headlineText,
        padding,
        img.height + padding + headlineFontSize * 0.8,
        img.width - padding * 2,
      );

      // Tagline
      if (tagline) {
        ctx.font = `400 italic ${taglineFontSize}px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`;
        ctx.fillStyle = '#666666';
        ctx.fillText(
          tagline,
          padding,
          img.height + padding + headlineFontSize + taglineFontSize * 0.8 + 4,
          img.width - padding * 2,
        );
      }

      canvas.toBlob((blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = 'generated-marketing-image.png';
          link.click();
          URL.revokeObjectURL(url);
        }
      }, 'image/png');
    };

    img.onerror = () => {
      plainDownload(imageUrl);
    };

    img.src = imageUrl;
  } catch {
    plainDownload(imageUrl);
  }
}

function plainDownload(url: string) {
  const link = document.createElement('a');
  link.href = url;
  link.download = 'generated-image.png';
  link.click();
}
