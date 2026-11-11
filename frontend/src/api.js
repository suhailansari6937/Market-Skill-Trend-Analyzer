const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
export function token(){ return localStorage.getItem('token'); }
export async function request(path, options={}) {
  const headers = {...(options.headers || {})};
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  if (token()) headers.Authorization = `Bearer ${token()}`;
  const res = await fetch(`${API}/api/v1${path}`, {...options, headers});
  const data = await res.json().catch(()=>({detail:'Unexpected server response'}));
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}
export { API };
