import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Container, Row, Col, Card, Form, Button, Alert } from 'react-bootstrap';

export default function LoginPage() {
  const { login } = useContext(AuthContext);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await login(email, password);
    if (success) {
      navigate('/profile');
    } else {
      setError('Invalid email or password');
    }
  };

  return (
    <Container className="d-flex flex-column justify-content-center align-items-center min-vh-100 py-5">
      <Row className="w-100 justify-content-center mb-4">
        <Col xs={12} md={6} lg={4} className="text-center">
          <h2 className="fw-bold mb-2">Welcome Back to DevCareer</h2>
          <p className="text-muted">
            Or <Link to="/signup" className="text-decoration-none">create a new account</Link>
          </p>
        </Col>
      </Row>

      <Row className="w-100 justify-content-center">
        <Col xs={12} md={8} lg={5}>
          <Card className="shadow-sm">
            <Card.Body className="p-4 p-md-5">
              <Form onSubmit={handleSubmit}>
                {error && <Alert variant="danger">{error}</Alert>}
                
                <Form.Group className="mb-3" controlId="formBasicEmail">
                  <Form.Label>Email address</Form.Label>
                  <Form.Control 
                    type="email" 
                    placeholder="Enter email" 
                    required
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                  />
                </Form.Group>

                <Form.Group className="mb-4" controlId="formBasicPassword">
                  <Form.Label>Password</Form.Label>
                  <Form.Control 
                    type="password" 
                    placeholder="Password" 
                    required
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                  />
                </Form.Group>

                <div className="d-grid">
                  <Button variant="primary" type="submit" size="lg">
                    Sign in
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}
