const list = document.getElementById('projects');
const messageEl = document.getElementById('message');

function showMessage(text, type = 'info') {
  messageEl.textContent = text;
  messageEl.className = `message ${type}`;
}

function clearMessage() {
  messageEl.textContent = '';
  messageEl.className = 'message hidden';
}

async function loadProjects() {
  showMessage('Loading...');
  try {
    const res = await fetch('/api/projects');
    if (!res.ok) throw new Error();
    const data = await res.json();
    list.innerHTML = '';
    if (data.projects.length === 0) {
      const empty = document.createElement('li');
      empty.textContent = 'No projects yet';
      empty.className = 'empty';
      list.appendChild(empty);
    } else {
      data.projects.forEach(project => {
        const item = document.createElement('li');
        const header = document.createElement('div');
        header.className = 'project-header';
        const title = document.createElement('h2');
        title.textContent = project.name;
        header.appendChild(title);
        const del = document.createElement('button');
        del.textContent = 'Delete';
        del.addEventListener('click', () => deleteProject(project.id, project.name));
        header.appendChild(del);
        item.appendChild(header);

        const meta = document.createElement('p');
        meta.textContent = `ID: ${project.id} | Updated: ${project.updated_at ?? 'never'}`;
        item.appendChild(meta);

        const branches = document.createElement('ul');
        project.branches.forEach(branch => {
          const bi = document.createElement('li');
          bi.textContent = `${branch.name} (${branch.id}) - ${branch.steps.length} steps`;
          branches.appendChild(bi);
        });
        item.appendChild(branches);
        list.appendChild(item);
      });
    }
    clearMessage();
  } catch {
    showMessage('Failed to load projects', 'error');
  }
}

async function createProject(name) {
  try {
    const resp = await fetch('/api/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    if (!resp.ok) throw new Error();
    showMessage('Project created', 'success');
    loadProjects();
  } catch {
    showMessage('Failed to create project', 'error');
  }
}

async function deleteProject(id, name) {
  if (!confirm(`Delete project "${name}"?`)) return;
  try {
    const resp = await fetch(`/api/projects/${id}`, { method: 'DELETE' });
    if (!resp.ok) throw new Error();
    showMessage('Project deleted', 'success');
    loadProjects();
  } catch {
    showMessage('Failed to delete project', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('refresh').addEventListener('click', loadProjects);
  document.getElementById('create-form').addEventListener('submit', e => {
    e.preventDefault();
    const name = document.getElementById('new-name').value.trim();
    if (!name) return;
    document.getElementById('new-name').value = '';
    createProject(name);
  });
  loadProjects();
});

