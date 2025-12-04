import React from 'react';

interface SelectFieldProps {
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  options: { value: string; label: string }[];
  className?: string;
}

const SelectField: React.FC<SelectFieldProps> = ({
  label,
  value,
  onChange,
  options,
  className = '',
}) => (
  <div className={`mb-4 ${className}`}>
    <label className="mb-1.5 block text-xs font-medium uppercase tracking-[0.16em] text-slate-300">
      {label}
    </label>
    <div className="relative">
      <select
        value={value}
        onChange={onChange}
        className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2.5 pr-10 text-sm text-slate-100 outline-none transition-all duration-200 focus:border-neonCyan/80 focus:ring-2 focus:ring-neonCyan/30 hover:border-neonPurple/50 cursor-pointer appearance-none bg-[url('data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2212%22%20height%3D%2212%22%20viewBox%3D%220%200%2012%2012%22%3E%3Cpath%20fill%3D%22%2300f5ff%22%20d%3D%22M6%209L1%204h10z%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[length:1em] bg-[right_0.75rem_center]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2300f5ff' d='M6 9L1 4h10z'/%3E%3C/svg%3E")`,
        }}
      >
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
            className="bg-slate-900 text-slate-100 py-2"
          >
            {option.label}
          </option>
        ))}
      </select>
      {/* Custom arrow indicator */}
      <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
        <svg
          className="h-4 w-4 text-neonCyan transition-transform duration-200"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </div>
    </div>
  </div>
);

export default SelectField;

