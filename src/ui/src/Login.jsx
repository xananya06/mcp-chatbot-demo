import { useSession, useUser, useDescope, getSessionToken } from '@descope/react-sdk'
import { useCallback } from 'react'
import { Descope } from '@descope/react-sdk'
import App from './App';

const Login = () => {
  const { isAuthenticated, isSessionLoading } = useSession()
  const {isUserLoading } = useUser()

  const { user } = useUser()
  const { logout } = useDescope()
  const handleLogout = useCallback(() => {
    logout()
  }, [logout]);

  return <>
    {!isAuthenticated &&
      (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          backgroundColor: '#f0f2f5'
        }}>
          <div style={{
            width: '400px',
            padding: '2rem',
            border: '1px solid #ccc',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            backgroundColor: '#fff'
          }}>
            <Descope
              flowId="sign-up-or-in"
              onSuccess={(e) => console.log(e.detail.user)}
              onError={(e) => console.log('Log in failed!')}
            />
          </div>
        </div>
      )
    }

    {
      (isSessionLoading || isUserLoading) && <p>Loading...</p>
    }

    {!isUserLoading && isAuthenticated &&
      (
        <App
          user={user}
          handleLogout={handleLogout}
          sessionToken={getSessionToken()}
        />
      )
    }
  </>;
}

export default Login;