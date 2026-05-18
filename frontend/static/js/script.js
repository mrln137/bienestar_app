/**
 * Bienestar Universitario — Frontend
 * UI según prototipo + integración con API Flask + LangChain + PDF médico
 */

(function () {
    "use strict";

    const API_BASE = "";
    const NOMBRE_USUARIO = "Juan Pérez";
    const PRIMER_NOMBRE = NOMBRE_USUARIO.split(" ")[0];

    let usuarioId = localStorage.getItem("bienestar_usuario_id");
    let chatAbierto = false;
    let chatMinimizado = false;

    // --- Referencias DOM ---
    const el = {
        nombreUsuario: document.getElementById("nombre-usuario"),
        nombrePanel: document.getElementById("nombre-panel"),
        saludoChat: document.getElementById("saludo-chat"),
        fechaActual: document.getElementById("fecha-actual"),
        perfilTrigger: document.getElementById("perfil-trigger"),
        perfilMenu: document.getElementById("perfil-menu"),
        navLinks: document.querySelectorAll(".nav-link"),
        chatFab: document.getElementById("chat-fab"),
        chatVentana: document.getElementById("chat-ventana"),
        chatCerrar: document.getElementById("chat-cerrar"),
        chatMinimizar: document.getElementById("chat-minimizar"),
        chatMensajes: document.getElementById("chat-mensajes"),
        chatFormulario: document.getElementById("chat-formulario"),
        chatInput: document.getElementById("chat-input"),
        chatBtnEnviar: document.getElementById("chat-btn-enviar"),
        // PDF — se asignan después del DOMContentLoaded
        chatBtnPdf: null,
        chatInputPdf: null,
        btnTarjetas: document.querySelectorAll(".btn-tarjeta[data-prompt]"),
        seccionCitas: document.getElementById("citas"),
        listaCitas: document.getElementById("lista-citas"),
        btnRefrescarCitas: document.getElementById("btn-refrescar-citas"),
        cabeceraSitio: document.getElementById("cabecera-sitio"),
        cabeceraSpacer: document.getElementById("cabecera-spacer"),
    };

    // =========================================================================
    // Inicialización
    // =========================================================================
    function init() {
        establecerNombres();
        establecerFecha();
        initPerfilDropdown();
        initCabeceraScroll();
        initNavSecundario();
        initChat();
        initBotonesServicio();
        initMenuCitas();
        cargarCitas();
        inyectarBotonPdf();  // ← agrega el botón PDF al formulario del chat
    }

    function establecerNombres() {
        if (el.nombreUsuario) el.nombreUsuario.textContent = NOMBRE_USUARIO;
        if (el.nombrePanel) el.nombrePanel.textContent = NOMBRE_USUARIO;
        if (el.saludoChat) el.saludoChat.textContent = PRIMER_NOMBRE;
    }

    function establecerFecha() {
        if (!el.fechaActual) return;
        const opciones = {
            weekday: "long",
            year: "numeric",
            month: "long",
            day: "numeric",
        };
        const fecha = new Date().toLocaleDateString("es-CO", opciones);
        el.fechaActual.textContent =
            fecha.charAt(0).toUpperCase() + fecha.slice(1) + ".";
    }

    // =========================================================================
    // Menú perfil desplegable
    // =========================================================================
    function initPerfilDropdown() {
        if (!el.perfilTrigger || !el.perfilMenu) return;

        el.perfilTrigger.addEventListener("click", (e) => {
            e.stopPropagation();
            const abierto = el.perfilTrigger.getAttribute("aria-expanded") === "true";
            togglePerfil(!abierto);
        });

        document.addEventListener("click", () => togglePerfil(false));

        el.perfilMenu.addEventListener("click", (e) => {
            if (e.target.closest('a[href="#citas"]')) {
                e.preventDefault();
                mostrarSeccionCitas();
                togglePerfil(false);
            }
        });
    }

    function togglePerfil(abierto) {
        el.perfilTrigger.setAttribute("aria-expanded", String(abierto));
        el.perfilMenu.hidden = !abierto;
    }

    function mostrarSeccionCitas() {
        if (el.seccionCitas) {
            el.seccionCitas.hidden = false;
            el.seccionCitas.scrollIntoView({ behavior: "smooth" });
        }
    }

    // =========================================================================
    // Cabecera: encogimiento gradual y suave según scroll
    // =========================================================================
    function initCabeceraScroll() {
        if (!el.cabeceraSitio) return;

        const RANGO_SCROLL = 280;
        const navbar = el.cabeceraSitio.querySelector(".navbar-principal");
        const logos = el.cabeceraSitio.querySelectorAll(".logo-bienestar, .logo-pamplona");
        const avatar = el.cabeceraSitio.querySelector(".perfil-avatar");

        function smoothstep(t) {
            return t * t * (3 - 2 * t);
        }

        function medirDimensiones() {
            el.cabeceraSitio.style.setProperty("--progreso", "0");

            const altoExpandido = navbar ? navbar.offsetHeight : 200;
            el.cabeceraSitio.style.setProperty("--progreso", "1");
            const altoCompacto = navbar ? navbar.offsetHeight : 72;
            el.cabeceraSitio.style.setProperty("--progreso", "0");

            el.cabeceraSitio.style.setProperty("--navbar-alto-expandido", `${altoExpandido}px`);
            el.cabeceraSitio.style.setProperty("--navbar-alto-compacto", `${altoCompacto}px`);

            if (logos.length) {
                const logoExp = logos[0].getBoundingClientRect().height;
                el.cabeceraSitio.style.setProperty("--progreso", "1");
                const logoComp = logos[0].getBoundingClientRect().height;
                el.cabeceraSitio.style.setProperty("--progreso", "0");
                el.cabeceraSitio.style.setProperty("--logo-alto-expandido", `${logoExp}px`);
                el.cabeceraSitio.style.setProperty("--logo-alto-compacto", `${logoComp}px`);
            }

            if (avatar) {
                el.cabeceraSitio.style.setProperty("--progreso", "0");
                const avatarExp = avatar.getBoundingClientRect().width;
                el.cabeceraSitio.style.setProperty("--progreso", "1");
                const avatarComp = avatar.getBoundingClientRect().width;
                el.cabeceraSitio.style.setProperty("--progreso", "0");
                el.cabeceraSitio.style.setProperty("--avatar-expandido", `${avatarExp}px`);
            }

            actualizarCabecera();
        }

        function actualizarCabecera() {
            const raw = Math.min(1, Math.max(0, window.scrollY / RANGO_SCROLL));
            const progreso = smoothstep(raw);
            el.cabeceraSitio.style.setProperty("--progreso", progreso.toFixed(4));
        }

        let ticking = false;
        window.addEventListener(
            "scroll",
            () => {
                if (!ticking) {
                    window.requestAnimationFrame(() => {
                        actualizarCabecera();
                        ticking = false;
                    });
                    ticking = true;
                }
            },
            { passive: true }
        );

        window.addEventListener("resize", medirDimensiones);
        medirDimensiones();
    }

    // =========================================================================
    // Navegación secundaria — ítem activo
    // =========================================================================
    function initNavSecundario() {
        el.navLinks.forEach((link) => {
            link.addEventListener("click", (e) => {
                e.preventDefault();
                setNavActivo(link);
                const destino = link.getAttribute("href");
                if (destino && destino.startsWith("#")) {
                    const seccion = document.querySelector(destino);
                    if (seccion) {
                        seccion.scrollIntoView({ behavior: "smooth", block: "start" });
                    }
                }
            });
        });
    }

    function setNavActivo(linkActivo) {
        el.navLinks.forEach((l) => l.classList.remove("nav-link--activo"));
        linkActivo.classList.add("nav-link--activo");
    }

    // =========================================================================
    // Chat flotante — abrir, cerrar, minimizar
    // =========================================================================
    function initChat() {
        el.chatFab.addEventListener("click", toggleChat);
        el.chatCerrar.addEventListener("click", cerrarChat);
        el.chatMinimizar.addEventListener("click", minimizarChat);

        el.chatFormulario.addEventListener("submit", async (e) => {
            e.preventDefault();
            const texto = el.chatInput.value.trim();
            if (!texto) return;
            await enviarMensaje(texto);
            el.chatInput.value = "";
        });

        el.chatInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                el.chatFormulario.requestSubmit();
            }
        });
    }

    function toggleChat() {
        if (chatAbierto) {
            cerrarChat();
        } else {
            abrirChat();
        }
    }

    function abrirChat() {
        chatAbierto = true;
        chatMinimizado = false;
        el.chatVentana.hidden = false;
        el.chatVentana.classList.remove("chat-ventana--minimizada");
        el.chatFab.setAttribute("aria-expanded", "true");
        el.chatInput.focus();
    }

    function cerrarChat() {
        chatAbierto = false;
        chatMinimizado = false;
        el.chatVentana.hidden = true;
        el.chatVentana.classList.remove("chat-ventana--minimizada");
        el.chatFab.setAttribute("aria-expanded", "false");
    }

    function minimizarChat() {
        if (!chatAbierto) {
            abrirChat();
            return;
        }
        chatMinimizado = !chatMinimizado;
        el.chatVentana.classList.toggle("chat-ventana--minimizada", chatMinimizado);
    }

    // =========================================================================
    // Mensajes en el chat
    // =========================================================================
    function agregarMensaje(texto, tipo = "asistente") {
        const div = document.createElement("div");
        div.className = `mensaje mensaje--${tipo}`;
        const p = document.createElement("p");
        p.textContent = texto;
        div.appendChild(p);
        el.chatMensajes.appendChild(div);
        el.chatMensajes.scrollTop = el.chatMensajes.scrollHeight;
        return div;
    }

    function setEnviando(estado) {
        el.chatInput.disabled = estado;
        el.chatBtnEnviar.disabled = estado;
        if (el.chatBtnPdf) el.chatBtnPdf.disabled = estado;
    }

    async function enviarMensaje(texto) {
        agregarMensaje(texto, "usuario");
        const cargando = agregarMensaje("Analizando...", "asistente cargando");
        cargando.classList.add("mensaje--cargando");
        setEnviando(true);

        const payload = {
            mensaje: texto,
            nombre: NOMBRE_USUARIO,
        };
        if (usuarioId) payload.usuario_id = parseInt(usuarioId, 10);

        try {
            const res = await fetch(`${API_BASE}/api/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            cargando.remove();

            if (!res.ok) {
                agregarMensaje(data.error || "No pude procesar tu mensaje.", "sistema");
                return;
            }

            if (data.usuario_id) {
                usuarioId = String(data.usuario_id);
                localStorage.setItem("bienestar_usuario_id", usuarioId);
            }

            agregarMensaje(data.respuesta, "asistente");

            // Si el agente agendó una cita, refrescar la lista automáticamente
            if (/cita agendada|#\d+/i.test(data.respuesta)) {
                await cargarCitas();
            }

        } catch {
            cargando.remove();
            agregarMensaje(
                "Sin conexión al servidor. Verifica que el backend esté en ejecución.",
                "sistema"
            );
            agregarMensaje(respuestaLocal(texto), "asistente");
        } finally {
            setEnviando(false);
            el.chatInput.focus();
        }
    }

    function respuestaLocal(texto) {
        const t = texto.toLowerCase();
        if (/fiebre|dolor|cabeza|síntoma|malestar/.test(t)) {
            return "Por tus síntomas, te recomiendo agendar valoración en Salud. Prioridad según gravedad.";
        }
        if (/cita|agendar/.test(t)) {
            return "Puedo ayudarte a registrar una solicitud de cita. ¿Cuál es el motivo principal?";
        }
        return "Estoy en modo local. Cuando el servidor esté activo, conectaré con el asistente de IA.";
    }

    // =========================================================================
    // PDF médico — botón inyectado dinámicamente en el formulario del chat
    // =========================================================================
    function inyectarBotonPdf() {
        // Input de archivo oculto
        const inputPdf = document.createElement("input");
        inputPdf.type = "file";
        inputPdf.accept = ".pdf";
        inputPdf.id = "chat-input-pdf";
        inputPdf.style.display = "none";
        document.body.appendChild(inputPdf);

        // Botón visible al lado del input de texto
        const btnPdf = document.createElement("button");
        btnPdf.type = "button";
        btnPdf.id = "chat-btn-pdf";
        btnPdf.title = "Adjuntar examen médico (PDF)";
        btnPdf.textContent = "📎";
        btnPdf.style.cssText =
            "background:#9a1b24;border:none;cursor:pointer;font-size:1.2rem;padding:0 6px;border-radius:20px";

        // Insertar el botón ANTES del botón de enviar
        el.chatBtnEnviar.parentNode.insertBefore(btnPdf, el.chatBtnEnviar);

        // Guardar referencias
        el.chatBtnPdf = btnPdf;
        el.chatInputPdf = inputPdf;

        // Eventos
        btnPdf.addEventListener("click", () => inputPdf.click());
        inputPdf.addEventListener("change", async (e) => {
            const archivo = e.target.files[0];
            if (archivo) await subirPdfMedico(archivo);
            e.target.value = ""; // reset para poder subir el mismo archivo de nuevo
        });
    }

    async function subirPdfMedico(archivo) {
        abrirChat();
        agregarMensaje(`📄 ${archivo.name}`, "usuario");
        const cargando = agregarMensaje("Analizando tu PDF médico... un momento ⏳", "asistente cargando");
        cargando.classList.add("mensaje--cargando");
        setEnviando(true);

        const formData = new FormData();
        formData.append("pdf", archivo);
        formData.append("nombre", NOMBRE_USUARIO);
        if (usuarioId) formData.append("usuario_id", usuarioId);

        try {
            const res = await fetch(`${API_BASE}/api/chat/subir-pdf`, {
                method: "POST",
                body: formData,
                // NO poner Content-Type manual — el navegador lo pone con el boundary
            });
            const data = await res.json();
            cargando.remove();

            if (!res.ok) {
                agregarMensaje(`❌ Error: ${data.error}`, "sistema");
                return;
            }

            if (data.usuario_id) {
                usuarioId = String(data.usuario_id);
                localStorage.setItem("bienestar_usuario_id", usuarioId);
            }

            agregarMensaje(data.analisis, "asistente");

            // Si el backend devolvió prioridad sugerida, mostrar un hint
            if (data.prioridad_sugerida) {
                const etiquetas = { 1: "Alta 🔴", 2: "Media 🟡", 3: "Baja 🟢" };
                agregarMensaje(
                    `Puedo agendar una cita con prioridad ${etiquetas[data.prioridad_sugerida]} basada en tus exámenes. ` +
                    `Escribe "sí, agendar" para confirmar o dime el motivo si quieres cambiar algo.`,
                    "sistema"
                );
            }

        } catch {
            cargando.remove();
            agregarMensaje("❌ No se pudo analizar el PDF. ¿Está el servidor activo?", "sistema");
        } finally {
            setEnviando(false);
            el.chatInput.focus();
        }
    }

    // =========================================================================
    // Botones de tarjetas de servicio → abren chat con prompt
    // =========================================================================
    function initBotonesServicio() {
        el.btnTarjetas.forEach((btn) => {
            btn.addEventListener("click", async () => {
                const prompt = btn.getAttribute("data-prompt");
                abrirChat();
                if (prompt) await enviarMensaje(prompt);
            });
        });
    }

    // =========================================================================
    // Citas — integración API (solo lectura desde el frontend)
    // El agendamiento ahora lo maneja el agente LangChain en el backend
    // =========================================================================
    function initMenuCitas() {
        if (el.btnRefrescarCitas) {
            el.btnRefrescarCitas.addEventListener("click", cargarCitas);
        }
    }

    async function cargarCitas() {
        if (!el.listaCitas) return;
        try {
            const res = await fetch(`${API_BASE}/api/citas/listar`);
            const data = await res.json();
            if (res.ok) renderizarCitas(data.citas || []);
        } catch {
            /* backend offline */
        }
    }

    function renderizarCitas(citas) {
        el.listaCitas.innerHTML = "";
        if (!citas.length) {
            const li = document.createElement("li");
            li.textContent = "No hay citas registradas.";
            el.listaCitas.appendChild(li);
            return;
        }
        const etiquetas = { 1: "Alta", 2: "Media", 3: "Baja" };
        citas.forEach((c) => {
            const li = document.createElement("li");
            const fecha = c.fecha_creacion
                ? new Date(c.fecha_creacion).toLocaleString("es-CO")
                : "";
            li.innerHTML =
                `<span class="prioridad-badge prioridad-${c.prioridad}">P${c.prioridad} ${etiquetas[c.prioridad]}</span> ` +
                `${c.motivo} <small>(${c.estado} · ${fecha})</small>`;
            el.listaCitas.appendChild(li);
        });
    }

    document.addEventListener("DOMContentLoaded", init);
})();
