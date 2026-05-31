import { redirect } from "next/navigation"

const STREAMLIT_URL =
  process.env.NEXT_PUBLIC_STREAMLIT_URL ?? "http://127.0.0.1:8507"

/**
 * Splash and other UI link here; Next responds with a redirect to the Streamlit scanner.
 */
export default function LiveRedirectPage() {
  redirect(STREAMLIT_URL)
}
