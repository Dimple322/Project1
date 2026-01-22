import { useCallback, useState } from 'react';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000';

type UploadResult = {
  document_id: string;
  filename: string;
  sha256_hash: string;
  status: string;
  message?: string;
};

type UseFileUploadOptions = {
  onSuccess?: () => void;
};

export function useFileUpload(options: UseFileUploadOptions = {}) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const upload = useCallback(
    (file: File) =>
      new Promise<UploadResult>((resolve, reject) => {
        const formData = new FormData();
        formData.append('file', file);

        const request = new XMLHttpRequest();
        request.open('POST', `${API_BASE_URL}/ingest/file`, true);

        request.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            setProgress(Math.round((event.loaded / event.total) * 100));
          }
        });

        request.addEventListener('load', () => {
          setIsLoading(false);
          if (request.status >= 200 && request.status < 300) {
            try {
              const data = JSON.parse(request.responseText) as UploadResult;
              setError(null);
              setProgress(100);
              options.onSuccess?.();
              resolve(data);
            } catch (parseError) {
              const message = 'Failed to parse upload response';
              setError(message);
              reject(new Error(message));
            }
          } else {
            const message = request.responseText || 'Upload failed';
            setError(message);
            reject(new Error(message));
          }
        });

        request.addEventListener('error', () => {
          setIsLoading(false);
          const message = 'Network error during upload';
          setError(message);
          reject(new Error(message));
        });

        setIsLoading(true);
        setError(null);
        setProgress(0);
        request.send(formData);
      }),
    [options]
  );

  return { upload, isLoading, error, progress };
}
