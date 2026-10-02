// Server only. Never include a service-role credential in either app target.
import { createClient } from "npm:@supabase/supabase-js@2";
const reply = (status: number, message: string) => new Response(JSON.stringify({message}), {status, headers: {"Content-Type":"application/json"}});
Deno.serve(async request => {
  if (request.method !== "POST") return reply(405, "Method not allowed");
  const authorization = request.headers.get("Authorization");
  if (!authorization?.startsWith("Bearer ")) return reply(401, "Sign in required");
  const url = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) return reply(503, "Service unavailable");
  try {
    const admin = createClient(url, key, {auth:{persistSession:false,autoRefreshToken:false}});
    // Verify with Auth, never trust a client-supplied user id or merely decode a JWT.
    const {data, error} = await admin.auth.getUser(authorization.slice(7));
    if (error || !data.user) return reply(401, "Sign in required");
    const deletion = await admin.auth.admin.deleteUser(data.user.id);
    if (deletion.error) return reply(500, "Deletion could not be completed");
    return reply(200, "Account deleted");
  } catch { return reply(503, "Service unavailable"); }
});
