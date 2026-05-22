const React = require('react');

const BrowserRouter = ({ children }) => React.createElement('div', null, children);
const MemoryRouter = ({ children }) => React.createElement('div', null, children);
const Routes = ({ children }) => React.createElement('div', null, children);
const Route = ({ element }) => React.createElement('div', null, element);
const Link = ({ children, to, ...props }) => React.createElement('a', { href: to, ...props }, children);
const Navigate = () => null;

const useNavigate = () => jest.fn();
const useParams = () => ({});
const useLocation = () => ({ pathname: '/', search: '', hash: '', state: null });
const useSearchParams = () => [new URLSearchParams(), jest.fn()];

module.exports = {
  BrowserRouter,
  MemoryRouter,
  Routes,
  Route,
  Link,
  Navigate,
  useNavigate,
  useParams,
  useLocation,
  useSearchParams,
};
