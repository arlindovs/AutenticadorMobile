import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import axios from 'axios';


export default function LoginScreen({ navigation, route }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    // Recebe o host vindo da configuração, ou usa um padrão
    const apiHost = route.params?.apiHost || 'http://localhost:8000';

    const handleLogin = async () => {
        if (!username || !password) {
            Alert.alert('Erro', 'Preencha usuário e senha');
            return;
        }
        setLoading(true);
        try {
            // Substitua pelo endereço do seu backend!
            const res = await axios.post(`${apiHost}/login`, {
                username,
                password,
            });
            setLoading(false);

            // Salva o token JWT (poderia usar AsyncStorage depois)
            const token = res.data.access_token;
            navigation.replace('Totp', { token, apiHost });// Vai para a próxima tela já passando o token
        } catch (err) {
            setLoading(false);
            Alert.alert('Falha ao logar', err.response?.data?.detail || 'Erro de rede');
        }
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Autenticador Mobile</Text>
            <TextInput
                style={styles.input}
                placeholder="Usuário"
                autoCapitalize="none"
                value={username}
                onChangeText={setUsername}
            />
            <TextInput
                style={styles.input}
                placeholder="Senha"
                secureTextEntry
                value={password}
                onChangeText={setPassword}
            />
            <Button title="Entrar" onPress={handleLogin} disabled={loading} />
            {loading && <ActivityIndicator style={{ marginTop: 20 }} />}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1, justifyContent: 'center', alignItems: 'center', padding: 16, backgroundColor: '#f6f6f6'
    },
    title: {
        fontSize: 26, fontWeight: 'bold', marginBottom: 24
    },
    input: {
        width: '100%', padding: 12, borderWidth: 1, borderColor: '#bbb', borderRadius: 6, marginBottom: 14, backgroundColor: '#fff'
    }
});
