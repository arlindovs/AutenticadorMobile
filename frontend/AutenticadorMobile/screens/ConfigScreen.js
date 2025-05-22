import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Alert, Platform } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import axios from 'axios';

const dbTypes = [
    { label: 'SQLite', value: 'sqlite' },
    { label: 'MySQL', value: 'mysql' },
    { label: 'PostgreSQL', value: 'postgres' },
];

export default function ConfigScreen({ navigation }) {
    const [apiHost, setApiHost] = useState('http://localhost:8000'); // ajuste para o seu IP!
    const [dbType, setDbType] = useState('sqlite');
    const [host, setHost] = useState('');
    const [user, setUser] = useState('');
    const [password, setPassword] = useState('');
    const [port, setPort] = useState('');
    const [database, setDatabase] = useState('');
    const [dbPath, setDbPath] = useState('authenticator.db');

    const handleConfig = async () => {
        let configPayload;
        if (dbType === 'sqlite') {
            configPayload = { db_type: 'sqlite', db_path: dbPath || 'authenticator.db' };
        } else {
            configPayload = {
                db_type: dbType,
                host,
                user,
                password,
                port: port ? parseInt(port) : (dbType === 'mysql' ? 3306 : 5432),
                database: database || 'authenticator'
            };
        }

        try {
            await axios.post(`${apiHost}/config`, configPayload);
            Alert.alert('Configuração feita!', 'Agora você pode fazer login.');
            navigation.replace('Login', { apiHost }); // Passa o host para a tela de login
        } catch (err) {
            Alert.alert('Erro ao configurar', err.response?.data?.detail || 'Falha de conexão');
        }
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Configuração do Backend</Text>
            <TextInput
                style={styles.input}
                placeholder="Endereço da API (ex: http://192.168.0.100:8000)"
                value={apiHost}
                onChangeText={setApiHost}
                autoCapitalize="none"
            />

            <Text style={styles.label}>Tipo de Banco:</Text>
            {Platform.OS === 'android' ? (
                <Picker
                    selectedValue={dbType}
                    style={styles.input}
                    onValueChange={setDbType}>
                    {dbTypes.map(opt => (
                        <Picker.Item label={opt.label} value={opt.value} key={opt.value} />
                    ))}
                </Picker>
            ) : (
                <TextInput
                    style={styles.input}
                    placeholder="Tipo de banco (sqlite/mysql/postgres)"
                    value={dbType}
                    onChangeText={setDbType}
                    autoCapitalize="none"
                />
            )}

            {dbType === 'sqlite' ? (
                <TextInput
                    style={styles.input}
                    placeholder="Nome do arquivo SQLite"
                    value={dbPath}
                    onChangeText={setDbPath}
                    autoCapitalize="none"
                />
            ) : (
                <>
                    <TextInput
                        style={styles.input}
                        placeholder="Host do Banco"
                        value={host}
                        onChangeText={setHost}
                        autoCapitalize="none"
                    />
                    <TextInput
                        style={styles.input}
                        placeholder="Usuário do Banco"
                        value={user}
                        onChangeText={setUser}
                        autoCapitalize="none"
                    />
                    <TextInput
                        style={styles.input}
                        placeholder="Senha do Banco"
                        value={password}
                        onChangeText={setPassword}
                        secureTextEntry
                    />
                    <TextInput
                        style={styles.input}
                        placeholder="Porta"
                        keyboardType="number-pad"
                        value={port}
                        onChangeText={setPort}
                    />
                    <TextInput
                        style={styles.input}
                        placeholder="Nome do Banco"
                        value={database}
                        onChangeText={setDatabase}
                        autoCapitalize="none"
                    />
                </>
            )}

            <Button title="Salvar e Continuar" onPress={handleConfig} />
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, padding: 24, justifyContent: 'center', backgroundColor: '#f6f6f6' },
    title: { fontSize: 22, fontWeight: 'bold', marginBottom: 22 },
    label: { fontSize: 16, marginTop: 14, marginBottom: 4 },
    input: { padding: 10, borderWidth: 1, borderColor: '#bbb', borderRadius: 6, marginBottom: 14, backgroundColor: '#fff' }
});
