import { useState, useRef } from 'react';
import { Camera, User, Phone, Calendar, MapPin, Lock, Save, X, Stethoscope, Building, Clock } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent } from './ui/card';
import { useAuth } from './AuthContext';

const API_PATIENT = 'http://localhost:8000';
const API_DOCTOR = 'http://localhost:8003';

const ProfileSettings = ({ onClose }) => {
  const { user, token, userRole, updateUser } = useAuth();
  const isDoctor = userRole === 'doctor';
  const apiBase = isDoctor ? API_DOCTOR : API_PATIENT;
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const fileInputRef = useRef(null);
  
  // Different fields for patient vs doctor
  const [formData, setFormData] = useState(isDoctor ? {
    name: user?.name || '',
    phone: user?.phone || '',
    specialization: user?.specialization || '',
    clinic_name: user?.clinic_name || '',
    clinic_address: user?.clinic_address || '',
    working_hours_start: user?.working_hours_start || '09:00',
    working_hours_end: user?.working_hours_end || '17:00'
  } : {
    name: user?.name || '',
    phone: user?.phone || '',
    date_of_birth: user?.date_of_birth || '',
    gender: user?.gender || '',
    address: user?.address || ''
  });
  
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handlePasswordChange = (e) => {
    setPasswordData({ ...passwordData, [e.target.name]: e.target.value });
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    const formDataObj = new FormData();
    formDataObj.append('file', file);

    const endpoint = isDoctor ? '/auth/doctor/profile/image' : '/auth/profile/image';
    try {
      const res = await fetch(`${apiBase}${endpoint}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formDataObj
      });
      const data = await res.json();
      if (data.success) {
        updateUser(data.user);
        setMessage({ type: 'success', text: 'Profile image updated!' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to upload image' });
    }
    setLoading(false);
  };


  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    const endpoint = isDoctor ? '/auth/doctor/profile' : '/auth/profile';
    try {
      const res = await fetch(`${apiBase}${endpoint}`, {
        method: 'PUT',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (data.success) {
        updateUser(data.user);
        setMessage({ type: 'success', text: 'Profile updated successfully!' });
      } else {
        setMessage({ type: 'error', text: data.detail || 'Update failed' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to update profile' });
    }
    setLoading(false);
  };

  const handlePasswordUpdate = async (e) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage({ type: 'error', text: 'Passwords do not match' });
      return;
    }
    setLoading(true);
    setMessage({ type: '', text: '' });

    const endpoint = isDoctor ? '/auth/doctor/password' : '/auth/password';
    try {
      const res = await fetch(`${apiBase}${endpoint}`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          old_password: passwordData.old_password,
          new_password: passwordData.new_password
        })
      });
      const data = await res.json();
      if (data.success) {
        setMessage({ type: 'success', text: 'Password changed successfully!' });
        setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
      } else {
        setMessage({ type: 'error', text: data.detail || 'Password change failed' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to change password' });
    }
    setLoading(false);
  };


  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Profile Settings</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>
        
        <CardContent className="p-6 space-y-6">
          {message.text && (
            <div className={`p-3 rounded-lg text-sm ${
              message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              {message.text}
            </div>
          )}

          {/* Profile Image */}
          <div className="flex flex-col items-center">
            <div className="relative">
              <div className="w-24 h-24 rounded-full bg-muted flex items-center justify-center overflow-hidden border-4 border-primary/20">
                {user?.profile_image ? (
                  <img src={user.profile_image} alt="Profile" className="w-full h-full object-cover" />
                ) : (
                  <User className="w-10 h-10 text-muted-foreground" />
                )}
              </div>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="absolute bottom-0 right-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white shadow-lg hover:bg-primary/90"
              >
                <Camera className="w-4 h-4" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
            </div>
            <p className="text-sm text-muted-foreground mt-2">{user?.email}</p>
          </div>

          {/* Profile Form */}
          <form onSubmit={handleProfileUpdate} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-1 block">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input name="name" value={formData.name} onChange={handleChange} className="pl-10" placeholder="Your name" />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">Phone</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input name="phone" value={formData.phone} onChange={handleChange} className="pl-10" placeholder="+216 XX XXX XXX" />
                </div>
              </div>
            </div>

            {isDoctor ? (
              <>
                <div>
                  <label className="text-sm font-medium mb-1 block">Specialization</label>
                  <div className="relative">
                    <Stethoscope className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input name="specialization" value={formData.specialization} onChange={handleChange} className="pl-10" placeholder="e.g. Cardiology" />
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Clinic Name</label>
                    <div className="relative">
                      <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input name="clinic_name" value={formData.clinic_name} onChange={handleChange} className="pl-10" placeholder="Clinic name" />
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Clinic Address</label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input name="clinic_address" value={formData.clinic_address} onChange={handleChange} className="pl-10" placeholder="Clinic address" />
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Working Hours Start</label>
                    <div className="relative">
                      <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input type="time" name="working_hours_start" value={formData.working_hours_start} onChange={handleChange} className="pl-10" />
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Working Hours End</label>
                    <div className="relative">
                      <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input type="time" name="working_hours_end" value={formData.working_hours_end} onChange={handleChange} className="pl-10" />
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Date of Birth</label>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input type="date" name="date_of_birth" value={formData.date_of_birth} onChange={handleChange} className="pl-10" />
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Gender</label>
                    <select
                      name="gender"
                      value={formData.gender}
                      onChange={handleChange}
                      className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                    >
                      <option value="">Select gender</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-1 block">Address</label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                    <Input name="address" value={formData.address} onChange={handleChange} className="pl-10" placeholder="Your address" />
                  </div>
                </div>
              </>
            )}
            <Button type="submit" disabled={loading} className="w-full">
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </Button>
          </form>

          {/* Password Change */}
          <div className="border-t pt-6">
            <h3 className="font-medium mb-4 flex items-center gap-2">
              <Lock className="w-4 h-4" /> Change Password
            </h3>
            <form onSubmit={handlePasswordUpdate} className="space-y-4">
              <Input type="password" name="old_password" value={passwordData.old_password} onChange={handlePasswordChange} placeholder="Current password" />
              <Input type="password" name="new_password" value={passwordData.new_password} onChange={handlePasswordChange} placeholder="New password" />
              <Input type="password" name="confirm_password" value={passwordData.confirm_password} onChange={handlePasswordChange} placeholder="Confirm new password" />
              <Button type="submit" variant="outline" disabled={loading} className="w-full">
                Update Password
              </Button>
            </form>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ProfileSettings;