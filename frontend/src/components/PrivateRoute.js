import React from 'react';
import { Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';

const PrivateRoute = ({ children }) => {
  const { access } = useSelector((state) => state.auth);

  return access ? children : <Navigate to="/login" replace />;
};

export default PrivateRoute;