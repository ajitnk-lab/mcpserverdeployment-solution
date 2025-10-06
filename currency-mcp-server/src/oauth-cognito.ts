/**
 * OAuth handling functionality for MCP server authentication.
 * Provides OAuth 2.0 authorization code flow implementation.
 */

import * as jose from "jose";
import fetch from "node-fetch";
import { Request, Response, NextFunction } from "express";

/**
 * Validate a Cognito access token.
 */
export async function validateCognitoToken(
  token: string
): Promise<{ isValid: boolean; claims: any }> {
  const region = process.env.AWS_REGION || "us-west-2";
  const user_pool_id = process.env.COGNITO_USER_POOL_ID;

  // Get the JWKs from Cognito
  const jwks_url = `https://cognito-idp.${region}.amazonaws.com/${user_pool_id}/.well-known/jwks.json`;

  try {
    // Fetch the JWKS
    const jwks_response = await fetch(jwks_url);
    const jwks = (await jwks_response.json()) as { keys: any[] };

    // Get the key ID from the token header
    const { kid } = await jose.decodeProtectedHeader(token);
    if (!kid) {
      return { isValid: false, claims: {} };
    }

    // Find the correct key
    const key = jwks.keys.find((k) => k.kid === kid);
    if (!key) {
      return { isValid: false, claims: {} };
    }

    // Import the key
    const publicKey = await jose.importJWK(key, key.alg);

    // Verify the token
    const { payload } = await jose.jwtVerify(token, publicKey, {
      issuer: `https://cognito-idp.${region}.amazonaws.com/${user_pool_id}`,
    });

    return { isValid: true, claims: payload };
  } catch (error) {
    console.error("Token validation error:", error);
    return { isValid: false, claims: {} };
  }
}

/**
 * Express middleware to authenticate requests using Bearer token
 */
export async function authenticateToken(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  try {
    const { isValid, claims } = await validateCognitoToken(token);
    
    if (!isValid) {
      return res.status(403).json({ error: 'Invalid or expired token' });
    }

    // Add user info to request object
    (req as any).user = claims;
    next();
  } catch (error) {
    console.error('Authentication error:', error);
    return res.status(403).json({ error: 'Token validation failed' });
  }
}
