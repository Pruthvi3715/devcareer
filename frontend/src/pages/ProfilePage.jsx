import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Container, Row, Col, Card, Form, Button, Alert } from 'react-bootstrap';
import API_BASE from '../utils/api';

export default function ProfilePage() {
  const { user, token, fetchUserProfile, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    skills: '',
    job_level: '',
    company: '',
    primary_language: '',
    coding_style: '',
    schooling: '',
    linkedin_url: ''
  });
  
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Check auth
  useEffect(() => {
    if (!token) {
      navigate('/login');
    }
  }, [token, navigate]);

  // Load user data when available
  useEffect(() => {
    if (user) {
      setFormData({
        skills: user.skills || '',
        job_level: user.job_level || '',
        company: user.company || '',
        primary_language: user.primary_language || '',
        coding_style: user.coding_style || '',
        schooling: user.schooling || '',
        linkedin_url: user.linkedin_url || ''
      });
    }
  }, [user]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSuccessMsg('');
    setErrorMsg('');
    
    try {
      const response = await fetch(`${API_BASE}/user/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        setSuccessMsg('Profile updated successfully!');
        fetchUserProfile(); // Refresh Context
      } else {
        setErrorMsg('Failed to update profile.');
      }
    } catch (err) {
      setErrorMsg('An error occurred.');
    }
  };

  if (!user) {
    return (
      <Container className="d-flex justify-content-center align-items-center min-vh-100">
        <h4 className="text-muted">Loading...</h4>
      </Container>
    );
  }

  return (
    <Container className="py-5">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2 className="fw-bold mb-0">Your Developer Profile</h2>
        <Button 
          variant="outline-secondary" 
          onClick={() => { logout(); navigate('/'); }}
        >
          Logout
        </Button>
      </div>

      <Card className="shadow-sm">
        <Card.Body className="p-4 p-md-5">
          <Form onSubmit={handleSave}>
            {successMsg && <Alert variant="success">{successMsg}</Alert>}
            {errorMsg && <Alert variant="danger">{errorMsg}</Alert>}

            <Row className="mb-3">
              <Form.Group as={Col} xs={12} controlId="formEmail">
                <Form.Label>Email (Read Only)</Form.Label>
                <Form.Control 
                  type="text" 
                  disabled 
                  value={user.email} 
                />
              </Form.Group>
            </Row>

            <Row className="mb-3">
              <Form.Group as={Col} xs={12} md={6} controlId="formSkills">
                <Form.Label>Current Skills</Form.Label>
                <Form.Control 
                  type="text" 
                  name="skills"
                  value={formData.skills}
                  onChange={handleChange}
                  placeholder="e.g., React, Python, Docker" 
                />
              </Form.Group>

              <Form.Group as={Col} xs={12} md={6} controlId="formJobLevel">
                <Form.Label>Job Level</Form.Label>
                <Form.Select 
                  name="job_level"
                  value={formData.job_level}
                  onChange={handleChange}
                >
                  <option value="">Select Level</option>
                  <option value="Junior">Junior</option>
                  <option value="Mid-Level">Mid-Level</option>
                  <option value="Senior">Senior</option>
                  <option value="Lead/Principal">Lead / Principal</option>
                  <option value="Manager">Manager</option>
                </Form.Select>
              </Form.Group>
            </Row>

            <Row className="mb-3">
              <Form.Group as={Col} xs={12} md={6} controlId="formCompany">
                <Form.Label>Where are you working?</Form.Label>
                <Form.Control 
                  type="text" 
                  name="company"
                  value={formData.company}
                  onChange={handleChange}
                  placeholder="Company Name" 
                />
              </Form.Group>

              <Form.Group as={Col} xs={12} md={6} controlId="formLanguage">
                <Form.Label>Primary Language</Form.Label>
                <Form.Control 
                  type="text" 
                  name="primary_language"
                  value={formData.primary_language}
                  onChange={handleChange}
                  placeholder="e.g., Python, TypeScript" 
                />
              </Form.Group>
            </Row>

            <Row className="mb-4">
              <Form.Group as={Col} xs={12} controlId="formStyle">
                <Form.Label>Coding Environment & Style</Form.Label>
                <Form.Control 
                  type="text" 
                  name="coding_style"
                  value={formData.coding_style}
                  onChange={handleChange}
                  placeholder="e.g., VS Code + Vim bindings" 
                />
              </Form.Group>
            </Row>

            <Row className="mb-4">
              <Form.Group as={Col} xs={12} md={6} controlId="formSchooling">
                <Form.Label>Schooling / Education</Form.Label>
                <Form.Control 
                  type="text" 
                  name="schooling"
                  value={formData.schooling}
                  onChange={handleChange}
                  placeholder="University/Bootcamp name" 
                />
              </Form.Group>

              <Form.Group as={Col} xs={12} md={6} controlId="formLinkedIn">
                <Form.Label>LinkedIn Profile</Form.Label>
                <Form.Control 
                  type="url" 
                  name="linkedin_url"
                  value={formData.linkedin_url}
                  onChange={handleChange}
                  placeholder="https://linkedin.com/in/you" 
                />
              </Form.Group>
            </Row>

            <div className="d-flex justify-content-end border-top pt-4">
              <Button variant="primary" type="submit" size="lg" className="px-5">
                Save Profile
              </Button>
            </div>
          </Form>
        </Card.Body>
      </Card>
    </Container>
  );
}
